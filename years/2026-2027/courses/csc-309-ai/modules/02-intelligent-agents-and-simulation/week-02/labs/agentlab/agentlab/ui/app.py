"""Responsive desktop explorer. A worker advances physics without blocking Tk.

The UI renders published snapshots only. Tk operations always stay on the main
thread. Reset creates a separate session, so an old worker cannot mutate it.
"""
from concurrent.futures import ThreadPoolExecutor
import copy
from dataclasses import replace
import math
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk,messagebox
from agentlab.simulations.balls import BallConfig
from agentlab.simulations.policies import AgentSettings,LABELS
from agentlab.simulations.session import Session,DT
from agentlab.ui.renderer import WorldRenderer,BG

FONT='Segoe UI' if sys.platform=='win32' else 'Helvetica'
PANEL='#111c2c';TEXT='#e9f1fa';MUTED='#91a6bc';ACCENT='#59e1dd'


def advance_batch(session,count,go,single=False):
    for _ in range(count):
        if session.done or (not single and not go.is_set()):break
        session.step()
    return copy.deepcopy(session)


class Application(tk.Tk):
    def __init__(self,config=BallConfig(),speed=1.,running=True,trails=True,settings=None,program='agents'):
        super().__init__()
        self.program=program
        self.title('AgentLab | '+('Sensing & Steering' if program=='agents' else 'Passive Particles'))
        self.geometry(f'{min(1280,self.winfo_screenwidth()-40)}x{min(860,self.winfo_screenheight()-80)}')
        self.minsize(820,600);self.configure(bg=BG)
        settings=settings or AgentSettings()
        if program=='particles':settings=replace(settings,policy='passive',sensing=False)
        self.live=Session(config,settings);self.view=copy.deepcopy(self.live)
        self.selected=1;self.running=running;self.closed=False;self.after_id=None
        self.executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='agentlab')
        self.future=None;self.future_session=None;self.go=threading.Event()
        if running:self.go.set()
        self.pending_single=False;self.accumulator=0.;self.limited=False;self.previous=time.perf_counter()
        self.speed=tk.DoubleVar(value=speed)
        self.shape=tk.StringVar(value=config.shape.title());self.count=tk.StringVar(value=str(config.count))
        self.seed=tk.StringVar(value=str(config.seed));self.radius=tk.StringVar(value=str(config.radius))
        self.aspect_ratio=tk.StringVar(value=str(config.aspect_ratio))
        self.policy=tk.StringVar(value=LABELS[settings.policy]);self.sensing=tk.BooleanVar(value=settings.sensing)
        self.sense_radius=tk.StringVar(value=str(settings.sensing_radius));self.angle=tk.StringVar(value=str(settings.steering_angle))
        self.horizon=tk.StringVar(value=str(settings.horizon));self.steps=tk.StringVar(value=str(settings.max_steps))
        self.mode=tk.StringVar(value=settings.mode)
        self.trails=tk.BooleanVar(value=trails);self.vectors=tk.BooleanVar(value=True);self.labels=tk.BooleanVar(value=False)
        self.sensor_overlay=tk.BooleanVar(value=program=='agents');self.predictions=tk.BooleanVar(value=False)
        self.show_panel=True
        self._style();self._build()
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.bind('<space>',self._space);self.bind('<Escape>',lambda e:self.set_running(False))
        self._frame()

    @property
    def sim(self):return self.view.world

    def _style(self):
        s=ttk.Style(self);s.theme_use('clam')
        s.configure('.',font=(FONT,10),background=PANEL,foreground=TEXT)
        s.configure('TButton',padding=(10,8),background='#23364c',borderwidth=0)
        s.map('TButton',background=[('active','#35536a'),('disabled','#192637')])
        s.configure('Accent.TButton',background=ACCENT,foreground='#08262b',font=(FONT,10,'bold'))
        s.map('Accent.TButton',background=[('active','#91eee8'),('disabled','#294d53')])
        s.configure('TEntry',fieldbackground='#1c2b40',foreground=TEXT,padding=5)
        s.configure('TCombobox',fieldbackground='#1c2b40',foreground=TEXT,padding=5)
        s.map('TCombobox',fieldbackground=[('readonly','#1c2b40')],foreground=[('readonly',TEXT)])
        s.configure('TCheckbutton',background=PANEL,foreground=TEXT)
        s.map('TCheckbutton',background=[('active',PANEL)])
        s.configure('TNotebook',background=PANEL,borderwidth=0)
        s.configure('TNotebook.Tab',padding=(10,8),background='#1c2b40')
        s.map('TNotebook.Tab',background=[('selected','#31505e')])
        s.configure('Horizontal.TScale',background=PANEL,troughcolor='#23364c')
        self.option_add('*TCombobox*Listbox.background','#1c2b40');self.option_add('*TCombobox*Listbox.foreground',TEXT)

    def label(self,parent,text,size=10,color=MUTED,bold=False,**kwargs):
        return tk.Label(parent,text=text,bg=parent.cget('bg'),fg=color,font=(FONT,size,'bold' if bold else 'normal'),**kwargs)

    def _tab(self,notebook,title):
        host=tk.Frame(notebook,bg=PANEL);notebook.add(host,text=title)
        bar=ttk.Scrollbar(host,orient='vertical');bar.pack(side='right',fill='y')
        cv=tk.Canvas(host,bg=PANEL,highlightthickness=0,yscrollcommand=bar.set);cv.pack(fill='both',expand=True)
        bar.configure(command=cv.yview)
        inner=tk.Frame(cv,bg=PANEL);item=cv.create_window(12,12,window=inner,anchor='nw')
        inner.bind('<Configure>',lambda e:cv.configure(scrollregion=cv.bbox('all')))
        cv.bind('<Configure>',lambda e:cv.itemconfigure(item,width=max(190,e.width-24)))
        def wheel(e):
            delta=(-1 if e.num==4 else 1) if getattr(e,'num',None) in (4,5) else (-1 if e.delta>0 else 1)
            cv.yview_scroll(delta,'units')
        def attach(widget):
            widget.bind('<MouseWheel>',wheel,add='+');widget.bind('<Button-4>',wheel,add='+');widget.bind('<Button-5>',wheel,add='+')
            for child in widget.winfo_children():attach(child)
        self.after_idle(lambda:attach(inner))
        return inner

    def field(self,parent,title,var,values=None):
        self.label(parent,title).pack(anchor='w',pady=(5,2))
        widget=ttk.Combobox(parent,textvariable=var,values=values,state='readonly') if values else ttk.Entry(parent,textvariable=var)
        widget.pack(fill='x',pady=(0,7));return widget

    def _build(self):
        self.grid_columnconfigure(0,weight=1);self.grid_rowconfigure(1,weight=1)
        header=tk.Frame(self,bg=BG);header.grid(row=0,column=0,sticky='ew',padx=20,pady=(14,10))
        self.label(header,'AGENTLAB  /  '+('AGENT EXPERIMENT' if self.program=='agents' else 'PASSIVE BASELINE'),10,ACCENT,True).pack(anchor='w')
        self.label(header,'Sensing & steering' if self.program=='agents' else 'Particles in motion',25,TEXT,True).pack(side='left')
        ttk.Button(header,text='Show / hide settings',command=self.toggle_panel).pack(side='right')
        body=tk.Frame(self,bg=BG);body.grid(row=1,column=0,sticky='nsew',padx=16)
        body.grid_rowconfigure(0,weight=1);body.grid_columnconfigure(0,weight=1)
        self.sidebar=tk.Frame(body,bg=PANEL,width=310);self.sidebar.grid(row=0,column=1,sticky='ns',padx=(12,0));self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0,weight=1);self.sidebar.grid_rowconfigure(1,weight=1)
        playback=tk.Frame(self.sidebar,bg=PANEL);playback.grid(row=0,column=0,sticky='ew',padx=12,pady=12)
        row=tk.Frame(playback,bg=PANEL);row.pack(fill='x')
        self.start_button=ttk.Button(row,text='Start',style='Accent.TButton',command=lambda:self.set_running(True));self.start_button.pack(side='left',expand=True,fill='x',padx=(0,4))
        self.stop_button=ttk.Button(row,text='Stop',command=lambda:self.set_running(False));self.stop_button.pack(side='left',expand=True,fill='x')
        row=tk.Frame(playback,bg=PANEL);row.pack(fill='x',pady=5)
        ttk.Button(row,text='Single step',command=self.single_step).pack(side='left',expand=True,fill='x',padx=(0,4))
        ttk.Button(row,text='Reset',command=self.reset).pack(side='left',expand=True,fill='x')
        self.speed_label=self.label(playback,'',10,TEXT);self.speed_label.pack(anchor='w',pady=(6,0))
        ttk.Scale(playback,from_=.1,to=4,variable=self.speed,command=self._speed_changed).pack(fill='x');self._speed_changed()
        tabs=ttk.Notebook(self.sidebar);tabs.grid(row=1,column=0,sticky='nsew',padx=6)
        world=self._tab(tabs,'World')
        self.field(world,'Boundary shape',self.shape,['Square','Rectangle','Circle','Triangle'])
        self.field(world,'Rectangle width / height (0.5-3)',self.aspect_ratio)
        self.field(world,'Particle count (1-120)',self.count)
        self.field(world,'Initial seed',self.seed)
        self.field(world,'Particle radius (world units)',self.radius)
        self.field(world,'Maximum steps',self.steps)
        self.field(world,'Run mode',self.mode,['survival','experiment'])
        self.label(world,'Survival: stops at first particle collision.\nExperiment: runs to the step limit.\nWall bounces are always allowed.',9,justify='left',wraplength=250).pack(anchor='w',pady=8)
        if self.program=='agents':
            agent=self._tab(tabs,'Agents')
            ttk.Checkbutton(agent,text='Enable sensing and steering',variable=self.sensing).pack(anchor='w',pady=(0,10))
            self.field(agent,'Policy',self.policy,list(LABELS.values()))
            self.field(agent,'Sensing radius (world units)',self.sense_radius)
            self.field(agent,'Steering angle (degrees)',self.angle)
            self.field(agent,'Prediction horizon (steps)',self.horizon)
            self.label(agent,'One-step policies always use horizon 1.\nPredictive policies use the setting above.\nAll decisions use the same snapshot.',9,justify='left',wraplength=250).pack(anchor='w',pady=8)
            tabs.select(1)
        display=self._tab(tabs,'View')
        for name,var in [('Motion trails',self.trails),('Velocity arrows',self.vectors),('Particle numbers',self.labels),('Selected sensing range',self.sensor_overlay),('Selected forecast path',self.predictions)]:
            ttk.Checkbutton(display,text=name,variable=var).pack(anchor='w',pady=6)
        self.label(display,'Click a particle to inspect its observation\nand most recent decision.\n\nThe world fits the available canvas.\nShapes keep their true proportions.\nWindow resizing never changes physics.',9,justify='left',wraplength=250).pack(anchor='w',pady=12)
        bottom=tk.Frame(self.sidebar,bg=PANEL);bottom.grid(row=2,column=0,sticky='ew',padx=12,pady=12)
        ttk.Button(bottom,text='Apply settings & reset',style='Accent.TButton',command=self.apply).pack(fill='x')
        self.label(bottom,'Settings apply on reset. Speed and view are live.',9,wraplength=260,justify='left').pack(pady=(7,0))
        left=tk.Frame(body,bg=BG);left.grid(row=0,column=0,sticky='nsew');left.grid_columnconfigure(0,weight=1);left.grid_rowconfigure(1,weight=1)
        self.world_title=self.label(left,'',10,MUTED,anchor='w');self.world_title.grid(row=0,column=0,sticky='ew',pady=(0,5))
        self.canvas=tk.Canvas(left,bg=BG,highlightthickness=0,width=300,height=300);self.canvas.grid(row=1,column=0,sticky='nsew')
        self.renderer=WorldRenderer(self.canvas);self.canvas.bind('<Button-1>',self.select_ball)
        info=tk.Frame(left,bg=PANEL);info.grid(row=2,column=0,sticky='ew',pady=(6,0));info.grid_columnconfigure(0,weight=1)
        self.metrics_label=self.label(info,'',11,TEXT,justify='left',anchor='w');self.metrics_label.grid(row=0,column=0,sticky='ew',padx=12,pady=(10,5))
        self.inspector=self.label(info,'',10,MUTED,justify='left',anchor='w');self.inspector.grid(row=1,column=0,sticky='ew',padx=12,pady=(0,10))
        info.bind('<Configure>',lambda e:(self.metrics_label.configure(wraplength=max(200,e.width-24)),self.inspector.configure(wraplength=max(200,e.width-24))))
        footer=tk.Frame(self,bg=BG);footer.grid(row=2,column=0,sticky='ew',padx=20,pady=10)
        self.status=self.label(footer,'',10,ACCENT,True);self.status.pack(side='left')
        ttk.Button(footer,text='Teaching guide',command=self.teaching_guide).pack(side='right')

    def toggle_panel(self):
        self.show_panel=not self.show_panel
        if self.show_panel:self.sidebar.grid()
        else:self.sidebar.grid_remove()

    def _speed_changed(self,*_):self.speed_label.configure(text=f'Playback speed: {self.speed.get():.2f}x')

    def _space(self,event):
        if not isinstance(self.focus_get(),(ttk.Entry,ttk.Combobox)):
            self.set_running(not self.running);return 'break'

    def set_running(self,value):
        self.running=bool(value) and not self.view.done
        if self.running:self.go.set()
        else:self.go.clear()
        self.accumulator=0.;self.previous=time.perf_counter()

    def _new_session(self,config,settings):
        new=Session(config,settings) # validate/spawn before replacing current state
        self.go.clear();self.go=threading.Event()
        if self.running:self.go.set()
        self.live=new;self.view=copy.deepcopy(new);self.selected=1
        self.accumulator=0.;self.limited=False;self.previous=time.perf_counter();self.pending_single=False

    def apply(self):
        try:
            config=BallConfig(self.shape.get().lower(),int(self.count.get()),int(self.seed.get()),float(self.radius.get()),float(self.aspect_ratio.get()))
            policy=next(k for k,v in LABELS.items() if v==self.policy.get())
            settings=AgentSettings(policy=policy if self.program=='agents' else 'passive',
                sensing=self.program=='agents' and self.sensing.get(),sensing_radius=float(self.sense_radius.get()),
                steering_angle=float(self.angle.get()),horizon=int(self.horizon.get()),max_steps=int(self.steps.get()),mode=self.mode.get())
            self._new_session(config,settings)
        except (ValueError,StopIteration) as exc:messagebox.showerror('Check settings',str(exc),parent=self)

    def reset(self):self._new_session(self.live.config,self.live.settings)

    def single_step(self):
        self.set_running(False)
        if not self.view.done:self.pending_single=True

    def select_ball(self,event):
        p=self.renderer.world_point(event.x,event.y)
        ball=min(self.sim.balls,key=lambda b:(b.position-p).length())
        if (ball.position-p).length()<max(ball.radius*2,12/self.renderer.scale):self.selected=ball.id

    def _frame(self):
        if self.closed:return
        now=time.perf_counter();elapsed=now-self.previous;self.previous=now
        if self.future is not None and self.future.done():
            try:
                view=self.future.result()
                if self.future_session is self.live:
                    self.view=view
                    if view.done:self.set_running(False)
            except Exception as exc:
                self.set_running(False);messagebox.showerror('Simulation error',str(exc),parent=self)
            self.future=None
        if self.running:
            self.accumulator+=elapsed*self.speed.get()
            if self.accumulator>.1:self.accumulator=.1;self.limited=True
        if self.future is None and not self.view.done:
            count=min(24,int(self.accumulator/DT)) if self.running else 0
            single=self.pending_single
            if single:count=1;self.pending_single=False
            if count:
                if not single:self.accumulator-=count*DT
                self.future_session=self.live
                self.future=self.executor.submit(advance_batch,self.live,count,self.go,single)
        self.renderer.draw(self.sim,self.selected,self.trails.get(),self.vectors.get(),self.labels.get(),
            self.view.settings,self.view.inspection,self.sensor_overlay.get(),self.predictions.get())
        r=self.view.result();s=self.view.settings
        effective=(1 if s.policy.startswith('reactive') else s.horizon) if s.sensing and s.policy!='passive' else 'off'
        self.world_title.configure(text=f'{self.sim.config.shape.upper()} / {len(self.sim.balls)} PARTICLES / SEED {self.sim.config.seed}')
        survival=f'{r["survival_steps"]} steps'
        if r['censored']:survival+=' (no collision yet)'
        self.metrics_label.configure(text=f'Step {self.sim.ticks:,} / {s.max_steps:,}   |   Time {self.sim.time:.2f}s\nSurvival: {survival}   |   Particle collisions: {self.sim.pair_collisions}')
        b=self.sim.balls[self.selected-1];d=self.view.inspection.get(b.id,{})
        turn={-1:'left',0:'straight',1:'right'}.get(d.get('action',0))
        self.inspector.configure(text=f'Particle {b.id:03}  |  speed {b.velocity.length():.3f}  |  sees {len(d.get("neighbours",[]))}  |  threats {len(d.get("threats",[]))}\nLast decision: {turn} - {d.get("reason","Awaiting first observation")}')
        status=self.view.reason if self.view.done else ('RUNNING' if self.running else 'STOPPED')
        active=LABELS[s.policy] if s.sensing and s.policy!='passive' else 'Passive / sensing off'
        self.status.configure(text=f'{status}  |  {active}  |  Horizon {effective}'+('  |  Workload limited' if self.limited else ''))
        self.start_button.configure(state='disabled' if self.running or self.view.done else 'normal')
        self.stop_button.configure(state='normal' if self.running else 'disabled')
        self.after_id=self.after(16,self._frame)

    def teaching_guide(self):
        window=tk.Toplevel(self);window.title('AgentLab | Concepts');window.geometry('660x540')
        text=tk.Text(window,bg=PANEL,fg=TEXT,font=(FONT,12),wrap='word',padx=22,pady=22,relief='flat');text.pack(fill='both',expand=True)
        text.insert('1.0','PEAS IN THIS EXPERIMENT\n\nPerformance: survive as many simulation steps as possible before the first particle collision. Experiment mode also counts collision events through the limit.\n\nEnvironment: the bounded world, other particles and physical collision rules. Walls may be hit.\n\nActuator: one fixed left/right turn, or no turn, per step. Steering preserves speed; physical collisions can change individual speeds.\n\nSensor: own state and neighbour positions/velocities inside R. The engine knows the whole world; agents use local observations.\n\nPOLICIES\nRandom policies turn randomly when a no-steering forecast predicts contact. Robust policies compare three actions against neighbours’ three immediate responses.\n\nA forecast applies one turn now, then coasts with wall reflections. It does not branch at future steps or model other neighbours colliding. Decisions are recomputed each real step.\n\nDisable sensing and Apply to reproduce passive behaviour. For comparisons use evaluate.py, which reuses the same seed set for every policy.\n\nReset repeats the applied seed. View/speed changes do not alter the world. Resizing preserves shape proportions and experimental density.')
        text.configure(state='disabled')

    def close(self):
        self.closed=True;self.go.clear()
        if self.after_id:self.after_cancel(self.after_id)
        self.executor.shutdown(wait=True,cancel_futures=True)
        self.destroy()
