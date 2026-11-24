"""Small Tk view: game rules stay in core.py; decisions stay in agents/.
A daemon worker calls agent methods; only the Tk thread touches widgets.
"""
import json
import math
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from .pacman import Pacman
from .agents import AGENTS
from .worlds import MAPS, SPECIALS

BG='#08111f'; FLOOR='#101c2d'; WALL='#193964'; EDGE='#3975b9'
TEXT='#e9f3ff'; MUTED='#a0b3c8'; CYAN='#51d6d1'; GOLD='#ffd158'

class ClassroomApp(tk.Tk):
    def __init__(self, pacman, agent=None):
        super().__init__()
        self.title('Pacman Classroom | Observe - Decide - Act')
        self.geometry('1280x900'); self.minsize(820,600); self.configure(bg=BG)
        self.pacman = pacman
        self.custom_agent = agent
        self.agent = None
        self.game = pacman.new_game()
        self.running = False; self.initialized = False; self.busy = False
        self.pending_action = None; self.result_queue = queue.Queue(); self.epoch = 0
        self.held = []; self.tap = None; self.next_tick = 0; self.closed = False
        self.flash_until = 0; self.face = 'R'; self.last_message = 'Ready. Choose a mode, then Start.'
        self.worker = None
        self.job_kind = ''
        self.mode = tk.StringVar(value='custom' if agent is not None else 'human')
        self.world_choice = tk.StringVar(value='Choose a world...')
        self.tick_ms = tk.IntVar(value=pacman.tick_ms)
        self.sound = tk.BooleanVar(value=False)
        self.status_text = tk.StringVar()
        self.detail_text = tk.StringVar()
        self.build()
        self.bind('<KeyPress>',self.key_down); self.bind('<KeyRelease>',self.key_up)
        self.bind('<FocusOut>',lambda e: self.clear_keys())
        self.protocol('WM_DELETE_WINDOW',self.close)
        for w in self.pacman.warnings: print('Config:',w,flush=True)
        self.after(20,self.loop)

    def build(self):
        style=ttk.Style(self); style.theme_use('clam')
        style.configure('TButton',font=('Arial',10),background='#203754',foreground=TEXT,padding=5)
        style.map('TButton',background=[('active','#305272')])
        style.configure('TCombobox',fieldbackground='#203754',foreground=TEXT,background='#203754')
        bar=tk.Frame(self,bg=BG); bar.pack(fill='x',padx=12,pady=(8,2))
        brand=tk.Label(bar,text='PACMAN / CLASSROOM',bg=BG,fg=CYAN,font=('Arial',14,'bold'))
        brand.pack(side='left')
        bar.bind('<Configure>',lambda e:brand.config(text='PACMAN' if e.width<1050 else 'PACMAN / CLASSROOM'))
        ttk.Button(bar,text='Config / raw arrays',command=self.editor).pack(side='right',padx=3)
        ttk.Button(bar,text='Reset',command=self.reset).pack(side='right',padx=3)
        ttk.Button(bar,text='Stop',command=self.stop).pack(side='right',padx=3)
        ttk.Button(bar,text='Pause',command=self.pause).pack(side='right',padx=3)
        ttk.Button(bar,text='Step',command=self.single_step).pack(side='right',padx=3)
        ttk.Button(bar,text='Start',command=self.start).pack(side='right',padx=3)
        row=tk.Frame(self,bg=BG); row.pack(fill='x',padx=12,pady=2)
        worlds=[f'Lesson {i}' for i in SPECIALS]+[f'World {i}: {name}' for i,(name,_) in enumerate(MAPS,1)]+['Random maze']
        ttk.Combobox(row,textvariable=self.world_choice,values=worlds,width=25,state='readonly').pack(side='left')
        ttk.Button(row,text='Load',command=self.load_world).pack(side='left',padx=(4,14))
        modes=['human']+list(AGENTS)+(['custom'] if self.custom_agent is not None else [])
        ttk.Combobox(row,textvariable=self.mode,values=modes,width=18,state='readonly').pack(side='left')
        tk.Label(row,text=' Tick ms ',bg=BG,fg=TEXT).pack(side='left')
        tk.Spinbox(row,from_=40,to=5000,increment=50,textvariable=self.tick_ms,width=5).pack(side='left')
        tk.Checkbutton(row,text='Sound',variable=self.sound,bg=BG,fg=MUTED,selectcolor=BG).pack(side='left',padx=8)
        tk.Label(self,textvariable=self.status_text,bg=BG,fg=TEXT,font=('Arial',13,'bold'),anchor='w').pack(fill='x',padx=14,pady=3)
        self.canvas=tk.Canvas(self,bg=BG,highlightthickness=0)
        self.canvas.pack(fill='both',expand=True,padx=8,pady=2)
        self.canvas.bind('<Button-1>',lambda e:self.canvas.focus_set())
        tk.Label(self,textvariable=self.detail_text,bg=BG,fg=MUTED,font=('Arial',10),anchor='w').pack(fill='x',padx=12,pady=(2,6))

    def clear_keys(self):
        self.held=[]; self.tap=None

    def key_down(self,e):
        if isinstance(e.widget,(tk.Entry,tk.Text,tk.Spinbox,ttk.Entry,ttk.Combobox)):
            return
        key=e.keysym.lower()
        if key=='escape': self.pause(); return
        action={'left':'L','right':'R','up':'U','down':'D','l':'L','r':'R','u':'U','d':'D','s':'S','space':'S'}.get(key)
        if action:
            self.tap=action
            if action in self.held: self.held.remove(action)
            self.held.append(action)
            return 'break'

    def key_up(self,e):
        action={'left':'L','right':'R','up':'U','down':'D','l':'L','r':'R','u':'U','d':'D','s':'S','space':'S'}.get(e.keysym.lower())
        if action in self.held: self.held.remove(action)

    def interval(self):
        try: return max(40,min(5000,int(self.tick_ms.get())))/1000
        except (ValueError,tk.TclError): return .25

    def invalidate(self):
        if self.agent is not None and hasattr(self.agent,'cancel'): self.agent.cancel.set()
        self.epoch+=1; self.busy=False; self.pending_action=None
        self.running=False; self.clear_keys()

    def reset(self):
        self.invalidate(); self.game=self.pacman.new_game(); self.initialized=False; self.agent=None
        self.face='R'; self.last_message='Reset. Press Start.'

    def pause(self):
        self.running=False; self.clear_keys(); self.last_message='Paused. No tick costs while paused.'

    def stop(self):
        self.invalidate(); self.game.status='stopped'; self.last_message='Stopped. Reset to start again.'

    def start(self):
        if self.game.status not in ('ready','running'): return
        self.canvas.focus_set()
        self.running=True; self.next_tick=time.perf_counter()+self.interval()
        if self.initialized: return
        # Do not overlap a non-cooperative custom worker with a new session.
        if self.worker is not None and self.worker.is_alive():
            self.running=False; self.last_message='Previous agent still computing; wait for it to finish.'; return
        name=self.mode.get()
        self.agent=self.custom_agent if name=='custom' else (AGENTS[name]() if name!='human' else None)
        self.active_mode=name
        self.initialized=True
        if self.agent is not None:
            if hasattr(self.agent,'cancel'): self.agent.cancel.clear()
            agent=self.agent; pos=self.game.position; foods=sorted(self.game.foods); grid=[r[:] for r in self.game.grid]
            self.submit('init',lambda:agent.init(pos,foods,grid))
        else: self.last_message='Human play: arrows or L/R/U/D. Release to wait; S/Space stops.'

    def submit(self,kind,work):
        self.busy=True; self.job_kind=kind; token=self.epoch
        def task():
            try: self.result_queue.put((token,kind,work(),None))
            except Exception as error: self.result_queue.put((token,kind,None,str(error)))
        self.worker=threading.Thread(target=task,daemon=True); self.worker.start()

    def single_step(self):
        if not self.initialized:
            self.start(); self.running=False
            self.last_message='Initialized. Press Step after planning finishes.'
            return
        self.pause()
        if self.busy or self.game.status not in ('ready','running'): return
        if self.agent is None: self.apply_action('S')
        elif self.pending_action is not None:
            action=self.pending_action; self.pending_action=None; self.apply_action(action)
        else:
            pos,foods=self.game.position,sorted(self.game.foods)
            agent=self.agent
            self.submit('step',lambda:agent.nextAction(pos,foods))

    def apply_action(self,action):
        try: event=self.game.step(action)
        except Exception as error:
            self.running=False; self.game.status='error'; self.last_message=str(error); return
        if action.upper()!='S': self.face=action.upper()
        if event['bump']:
            self.flash_until=time.perf_counter()+.3; self.last_message='BONK! Wall blocked the action; tick cost still applies.'
            if self.sound.get(): self.bell()
        elif event['ate']: self.last_message=f'Food collected! +{self.game.scoring.food_reward:g}'
        else: self.last_message=f'Action {action.upper()} | -{self.game.scoring.step_cost:g} per tick'
        if self.game.status in ('won','lost'): self.running=False
        self.next_tick=time.perf_counter()+self.interval()

    def loop(self):
        if self.closed: return
        while True:
            try: token,kind,result,error=self.result_queue.get_nowait()
            except queue.Empty: break
            if token!=self.epoch: continue
            self.busy=False; self.next_tick=time.perf_counter()+self.interval()
            if error:
                self.running=False; self.game.status='error'; self.last_message=error
            elif kind in ('action','step'):
                if kind=='step' or self.running: self.apply_action(result)
                else: self.pending_action=result
            else: self.last_message='Agent initialized. Plan ready.'
        if self.running and not self.busy and time.perf_counter()>=self.next_tick:
            if self.pending_action is not None:
                action=self.pending_action; self.pending_action=None; self.apply_action(action)
            elif self.agent is None:
                action=self.tap or (self.held[-1] if self.held else 'S'); self.tap=None; self.apply_action(action)
            else:
                pos,foods=self.game.position,sorted(self.game.foods)
                agent=self.agent
                self.submit('action',lambda:agent.nextAction(pos,foods))
        self.render(); self.after(25,self.loop)

    def render(self):
        g=self.game; cv=self.canvas; cv.delete('all')
        width=max(1,cv.winfo_width()-12); height=max(1,cv.winfo_height()-12)
        cw,ch=width/len(g.grid[0]),height/len(g.grid)
        cell=min(cw,ch)
        for r,row in enumerate(g.grid):
            for c,v in enumerate(row):
                x,y=6+c*cw,6+r*ch
                cv.create_rectangle(x+1,y+1,x+cw-1,y+ch-1,fill=FLOOR if v else WALL,outline='#15263a' if v else EDGE)
        for r,c in g.foods:
            x,y=6+(c+.5)*cw,6+(r+.5)*ch; rad=max(2,cell*.10)
            cv.create_oval(x-rad*1.8,y-rad*1.8,x+rad*1.8,y+rad*1.8,fill='#344139',outline='')
            cv.create_oval(x-rad,y-rad,x+rad,y+rad,fill='#ffe6a4',outline='')
        if g.position is not None:
            r,c=g.position; x,y=6+(c+.5)*cw,6+(r+.5)*ch; rad=cell*.36
            bump=time.perf_counter()<self.flash_until
            if bump: x+=math.sin(time.perf_counter()*80)*4
            angle={'R':0,'U':90,'L':180,'D':270}[self.face]
            mouth=22+8*math.sin(time.perf_counter()*12) if self.running else 24
            cv.create_arc(x-rad,y-rad,x+rad,y+rad,start=angle+mouth,extent=360-2*mouth,fill='#ff8b8b' if bump else GOLD,outline='',style='pieslice')
            ex=x+math.cos(math.radians(angle+70))*rad*.5; ey=y-math.sin(math.radians(angle+70))*rad*.5
            cv.create_oval(ex-2,ey-2,ex+2,ey+2,fill=BG,outline='')
            if bump: cv.create_text(x,y-rad-8,text='BONK!',fill='#ff9a9a',font=('Arial',12,'bold'))
        label='THINKING (clock paused)' if self.busy else ('RUNNING' if self.running else g.status.upper())
        self.status_text.set(f'{label}   |   SCORE {g.score:g}   |   STEP {g.tick}   |   FOOD LEFT {len(g.foods)}   |   {self.pacman.title}')
        stats=getattr(self.agent,'stats',{}) if self.agent else {}
        info=f' | expanded {stats.get("expanded",0):,} | plan {stats.get("plan_length",0)}' if stats else ''
        self.detail_text.set(self.last_message+info)
        if g.status in ('won','lost','stopped','invalid','error'):
            title={'won':'ALL FOOD COLLECTED','lost':'OUT OF POINTS','stopped':'STOPPED','invalid':'AGENT POSITION INVALID','error':'AGENT STOPPED'}[g.status]
            x,y=cv.winfo_width()/2,cv.winfo_height()/2
            cv.create_rectangle(x-230,y-42,x+230,y+42,fill=BG,outline=CYAN,width=2)
            cv.create_text(x,y-10,text=title,fill=CYAN if g.status=='won' else GOLD,font=('Arial',21,'bold'))
            cv.create_text(x,y+20,text='Reset to play again | Config to inspect the world',fill=MUTED,font=('Arial',11))

    def load_world(self):
        self.pause()
        option=self.world_choice.get()
        if option=='Choose a world...': return
        if option=='Random maze': self.editor(random_mode=True); return
        try:
            if option.startswith('Lesson'): p=Pacman.special(int(option.split()[1]),tick_ms=int(self.interval()*1000))
            else: p=Pacman.world(int(option.split()[1].rstrip(':')),tick_ms=int(self.interval()*1000))
            self.pacman=p; self.reset()
        except Exception as e: messagebox.showerror('World',str(e),parent=self)

    def editor(self,random_mode=False):
        self.pause()
        dialog=tk.Toplevel(self); dialog.title('World configuration | zero-based [row, column]'); dialog.geometry('850x700'); dialog.configure(bg=BG)
        tk.Label(dialog,text='0 = wall   1 = floor | Edges become walls | Invalid food is ignored | Invalid agent is hidden',bg=BG,fg=TEXT).pack(pady=8)
        form=tk.Frame(dialog,bg=BG); form.pack(fill='x',padx=10)
        vars={}
        for name,value in [('Width',21),('Height',15),('Foods',4),('Seed',42)]:
            tk.Label(form,text=name,bg=BG,fg=TEXT).pack(side='left',padx=3)
            v=tk.StringVar(value=str(value)); vars[name]=v
            ttk.Entry(form,textvariable=v,width=5).pack(side='left')
        text_frame=tk.Frame(dialog,bg=BG); text_frame.pack(fill='both',expand=True,padx=10,pady=8)
        scroll=ttk.Scrollbar(text_frame); scroll.pack(side='right',fill='y')
        horizontal=ttk.Scrollbar(text_frame,orient='horizontal'); horizontal.pack(side='bottom',fill='x')
        editor=tk.Text(text_frame,yscrollcommand=scroll.set,xscrollcommand=horizontal.set,bg=FLOOR,fg=TEXT,insertbackground=CYAN,font=('Courier',11),wrap='none',undo=True)
        editor.pack(fill='both',expand=True)
        scroll.config(command=editor.yview); horizontal.config(command=editor.xview)
        def put(data):
            from .formatting import config_text
            editor.delete('1.0','end'); editor.insert('1.0',config_text(data))
        put(self.pacman.config)
        def generate():
            try:
                p=Pacman(width=int(vars['Width'].get()),height=int(vars['Height'].get()),food_count=int(vars['Foods'].get()),seed=int(vars['Seed'].get()))
                put(p.config)
            except Exception as e: messagebox.showerror('Random world',str(e),parent=dialog)
        ttk.Button(form,text='Generate arrays',command=generate).pack(side='left',padx=8)
        def parsed():
            data=json.loads(editor.get('1.0','end'))
            scoring=data.get('scoring',{})
            return Pacman(data['grid'],data.get('foods',[]),data.get('agent'),
                          start_score=scoring.get('start',50),step_cost=scoring.get('step_cost',1),
                          food_reward=scoring.get('food_reward',50),tick_ms=int(self.interval()*1000))
        def apply():
            try:
                p=parsed(); put(p.config); self.pacman=p; self.reset()
                self.last_message='Configuration applied. Raw arrays normalized.'
                if p.warnings: messagebox.showinfo('Configuration normalized','\n'.join(p.warnings[:15]),parent=dialog)
                dialog.destroy()
            except Exception as e: messagebox.showerror('Configuration',str(e),parent=dialog)
        def copy_text(): self.clipboard_clear(); self.clipboard_append(editor.get('1.0','end-1c'))
        def save():
            try:
                p=parsed(); path=filedialog.asksaveasfilename(parent=dialog,defaultextension='.json',filetypes=[('JSON','*.json')])
                if path:
                    with open(path,'w',encoding='utf8') as f: json.dump(p.config,f,indent=2)
            except Exception as e: messagebox.showerror('Save',str(e),parent=dialog)
        def load():
            path=filedialog.askopenfilename(parent=dialog,filetypes=[('JSON','*.json')])
            if path:
                try:
                    with open(path,encoding='utf8') as f: put(json.load(f))
                except Exception as e: messagebox.showerror('Load',str(e),parent=dialog)
        buttons=tk.Frame(dialog,bg=BG); buttons.pack(fill='x',padx=10,pady=8)
        for label,command in [('Apply & reset',apply),('Copy arrays',copy_text),('Current state',lambda:put(self.game.raw())),('Initial config',lambda:put(self.pacman.config)),('Save JSON',save),('Load JSON',load)]:
            ttk.Button(buttons,text=label,command=command).pack(side='left',padx=3)
        if random_mode: generate()

    def close(self):
        self.closed=True; self.invalidate(); self.destroy()
