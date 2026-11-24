"""Tk explorer; only the worker mutates the live model, and Tk stays on main thread."""
import copy
import math
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import tkinter as tk
from tkinter import ttk,messagebox
from .model import Config,Colony,DT,WIDTH,HEIGHT,COLS,ROWS,NEST,NEST_RADIUS
from agentlab.ui.app import Application,FONT

BG='#09131f';PANEL='#112335';FG='#edf4fa';MUTED='#9eb3c8';TEAL='#55dfdb';GOLD='#ffcc81'

def advance(world,n):
    for _ in range(n):world.step()
    return copy.deepcopy(world)

class ForagingApp(tk.Tk):
    def __init__(self,config=Config(),speed=1,autostart=False):
        super().__init__();self.title('AgentLab | The Foraging Colony');self.geometry('1260x820');self.minsize(850,600);self.configure(bg=BG)
        Application._style(self)
        self.live=Colony(config);self.view=copy.deepcopy(self.live);self.running=autostart;self.selected=0
        self.pool=ThreadPoolExecutor(max_workers=1);self.future=None;self.future_world=None;self.closed=False;self.after_id=None
        self.speed=tk.DoubleVar(value=speed);self.show_field=tk.BooleanVar(value=True);self.sensors=tk.BooleanVar(value=True)
        self.show_ants=tk.BooleanVar(value=True);self.pheromones=tk.BooleanVar(value=config.pheromones);self.gain=tk.DoubleVar(value=3)
        self.vars={k:tk.StringVar(value=str(v)) for k,v in asdict(config).items() if k!='pheromones'}
        self.previous=time.perf_counter();self.credit=0;self.single=False;self.last_render=-1
        self.build();self.protocol('WM_DELETE_WINDOW',self.close);self.bind('<Escape>',lambda e:self.pause())
        self.canvas.bind('<Button-1>',self.select);self.loop()

    def label(self,parent,s,size=11,color=MUTED):
        return tk.Label(parent,text=s,bg=parent.cget('bg'),fg=color,font=(FONT,size),anchor='w',justify='left')

    def build(self):
        top=tk.Frame(self,bg=BG);top.pack(fill='x',padx=24,pady=(20,12))
        self.label(top,'AGENTLAB  /  COLLECTIVE BEHAVIOUR',10,TEAL).pack(anchor='w')
        self.label(top,'The foraging colony',27,FG).pack(anchor='w')
        self.label(top,'Local discoveries. Shared trails. Collective food collection.',11).pack(anchor='w')
        body=tk.Frame(self,bg=BG);body.pack(fill='both',expand=True,padx=20,pady=8)
        left=tk.Frame(body,bg=BG);left.pack(side='left',fill='both',expand=True,padx=(0,16))
        self.stats=self.label(left,'',12,FG);self.stats.pack(fill='x',pady=(0,8))
        self.canvas=tk.Canvas(left,bg=BG,highlightthickness=0);self.canvas.pack(fill='both',expand=True)
        self.inspect=self.label(left,'Click an ant to inspect its decision.',10);self.inspect.pack(fill='x',pady=8)
        self.chart=tk.Canvas(left,bg=PANEL,height=90,highlightthickness=0);self.chart.pack(fill='x')
        self.label(left,'TEAL: searching   GOLD: carrying food   CYAN FIELD: pheromone',9).pack(fill='x',pady=8)
        side=tk.Frame(body,bg=PANEL,width=310);side.pack(side='right',fill='y');side.pack_propagate(False)
        controls=tk.Frame(side,bg=PANEL);controls.pack(fill='x',padx=14,pady=12)
        ttk.Button(controls,text='Start',style='Accent.TButton',command=self.start).grid(row=0,column=0,sticky='ew')
        ttk.Button(controls,text='Pause',command=self.pause).grid(row=0,column=1,sticky='ew')
        ttk.Button(controls,text='Single step',command=self.step_once).grid(row=1,column=0,sticky='ew',pady=5)
        ttk.Button(controls,text='Reset seed',command=self.reset).grid(row=1,column=1,sticky='ew',pady=5)
        for k in range(2):controls.columnconfigure(k,weight=1)
        self.speed_label=self.label(side,'Playback 1.0×',11,FG);self.speed_label.pack(fill='x',padx=14)
        ttk.Scale(side,from_=.1,to=8,variable=self.speed).pack(fill='x',padx=14,pady=(3,9))
        nb=ttk.Notebook(side)
        world=self.tab(nb,'World');beh=self.tab(nb,'Behaviour');view=self.tab(nb,'View')
        for k,label in [('ants','Number of ants (1-500)'),('foods','Food sources (1-12)'),('food_units','Units per food source'),('seed','Random seed'),('ant_speed','Ant speed (world units / second)')]:self.entry(world,k,label)
        for k,label in [('sensor_distance','Pheromone sensing distance'),('sensor_angle','Sensor spread (degrees)'),('turn_angle','Maximum steering turn (degrees)'),('exploration','Exploration probability (0–1)'),('deposit','Deposit rate (units / second)'),('evaporation','Evaporation constant (per second)'),('diffusion','Diffusion rate (per second)')]:self.entry(beh,k,label)
        ttk.Checkbutton(beh,text='Enable pheromone communication',variable=self.pheromones).pack(anchor='w',pady=10)
        for label,var in [('Show pheromone field',self.show_field),('Show ants',self.show_ants),('Selected ant sensors',self.sensors)]:ttk.Checkbutton(view,text=label,variable=var).pack(anchor='w',pady=9)
        self.label(view,'Trail brightness (display only)',10).pack(anchor='w',pady=(10,0))
        ttk.Scale(view,from_=.3,to=8,variable=self.gain).pack(fill='x')
        self.label(view,'Ants know the nest direction.\nThey discover food locally.\nAnt-ant collisions are not modelled.',10).pack(anchor='w',pady=20)
        ttk.Button(side,text='Apply settings & reset',style='Accent.TButton',command=self.apply).pack(side='bottom',fill='x',padx=14,pady=12)
        self.label(side,'World and behaviour edits apply on reset.\nPlayback and view controls update live.',9).pack(side='bottom',padx=14,pady=(0,12))
        nb.pack(fill='both',expand=True,padx=10)

    def tab(self,nb,title):
        host=tk.Frame(nb,bg=PANEL);nb.add(host,text=title)
        bar=ttk.Scrollbar(host);bar.pack(side='right',fill='y')
        cv=tk.Canvas(host,bg=PANEL,highlightthickness=0,yscrollcommand=bar.set);cv.pack(side='left',fill='both',expand=True);bar.config(command=cv.yview)
        inner=tk.Frame(cv,bg=PANEL);win=cv.create_window((8,8),window=inner,anchor='nw')
        inner.bind('<Configure>',lambda e:cv.configure(scrollregion=cv.bbox('all')))
        cv.bind('<Configure>',lambda e:cv.itemconfigure(win,width=max(100,e.width-16)))
        return inner

    def entry(self,parent,key,label):
        self.label(parent,label,10).pack(anchor='w',pady=(10,3));ttk.Entry(parent,textvariable=self.vars[key]).pack(fill='x')

    def start(self):self.running=True;self.previous=time.perf_counter()
    def pause(self):self.running=False;self.credit=0
    def step_once(self):self.pause();self.single=True
    def reset(self):self.new_world(self.live.config)
    def new_world(self,config):
        world=Colony(config);self.pause();self.live=world;self.view=copy.deepcopy(world);self.selected=0;self.single=False
    def apply(self):
        try:
            values={k:type(v)(self.vars[k].get()) for k,v in asdict(Config()).items() if k!='pheromones'}
            self.new_world(Config(**values,pheromones=self.pheromones.get()))
        except ValueError as e:messagebox.showerror('Check settings',str(e),parent=self)

    def loop(self):
        if self.closed:return
        now=time.perf_counter();elapsed=min(.1,now-self.previous);self.previous=now
        if self.future and self.future.done():
            try:
                result=self.future.result()
                if self.future_world is self.live:self.view=result
            except Exception as e:self.pause();messagebox.showerror('Simulation error',str(e),parent=self)
            self.future=None
        if self.running and not self.view.done:self.credit=min(32,self.credit+elapsed*self.speed.get()/DT)
        if self.future is None and (self.single or self.credit>=1):
            n=1 if self.single else min(16,int(self.credit));self.credit=max(0,self.credit-n);self.single=False
            self.future_world=self.live;self.future=self.pool.submit(advance,self.live,n)
        if self.view.done:self.pause()
        self.render();self.after_id=self.after(33,self.loop)

    def transform(self):
        w=max(1,self.canvas.winfo_width());h=max(1,self.canvas.winfo_height());s=max(1,min((w-24)/WIDTH,(h-24)/HEIGHT))
        return (w-WIDTH*s)/2,(h-HEIGHT*s)/2,s

    def select(self,event):
        ox,oy,s=self.transform();x=(event.x-ox)/s;y=(event.y-oy)/s
        self.selected=min(range(len(self.view.ants)),key=lambda i:math.hypot(self.view.ants[i].x-x,self.view.ants[i].y-y))

    def render(self):
        w=self.view;cv=self.canvas;cv.delete('all');ox,oy,s=self.transform();xy=lambda x,y:(ox+x*s,oy+y*s)
        cv.create_rectangle(ox,oy,ox+WIDTH*s,oy+HEIGHT*s,fill='#0d1d2b',outline='#3f7d8c',width=2)
        if self.show_field.get():
            for i,v in enumerate(w.field):
                intensity=min(1,math.log1p(v*self.gain.get())/4)
                if intensity<.025:continue
                col='#%02x%02x%02x'%(int(13+65*intensity),int(29+190*intensity),int(43+180*intensity))
                x,y=xy(i%COLS*WIDTH/COLS,i//COLS*HEIGHT/ROWS)
                cv.create_rectangle(x,y,x+WIDTH/COLS*s+1,y+HEIGHT/ROWS*s+1,fill=col,outline='')
        nx,ny=xy(*NEST);r=NEST_RADIUS*s
        cv.create_oval(nx-r*1.7,ny-r*1.7,nx+r*1.7,ny+r*1.7,outline='#52678a',dash=(3,5))
        cv.create_oval(nx-r,ny-r,nx+r,ny+r,fill='#615baf',outline='#b3a4ff',width=2)
        cv.create_text(nx,ny+r+13,text='NEST',fill='#c4bcff',font=(FONT,9,'bold'))
        for j,f in enumerate(w.food):
            x,y=xy(f.x,f.y);r=(.012+.017*math.sqrt(f.remaining/f.initial))*s
            cv.create_oval(x-r,y-r,x+r,y+r,fill='#63ce94' if f.remaining else '#263d38',outline='#a4f5bf' if f.remaining else '#406051',width=2)
            cv.create_text(x,y+r+12,text=f'F{j+1} · {f.remaining}',fill='#b9e5c8',font=(FONT,9))
        if self.show_ants.get():
            for i,a in enumerate(w.ants):
                x,y=xy(a.x,a.y);co=GOLD if a.carrying else TEAL;dx=math.cos(a.heading);dy=math.sin(a.heading)
                cv.create_line(x-dx*4,y-dy*4,x+dx*5,y+dy*5,fill=co,width=2)
                cv.create_oval(x-2,y-2,x+2,y+2,fill=co,outline='')
                if a.carrying:cv.create_oval(x+dx*5-2,y+dy*5-2,x+dx*5+2,y+dy*5+2,fill='#baf4a0',outline='')
        a=w.ants[self.selected];x,y=xy(a.x,a.y);cv.create_oval(x-9,y-9,x+9,y+9,outline='white',dash=(2,3))
        if self.sensors.get() and not a.carrying:
            for sx,sy in w.samples(a):
                xx,yy=xy(sx,sy)
                if 0<=sx<=WIDTH and 0<=sy<=HEIGHT:cv.create_line(x,y,xx,yy,fill='#67878e',dash=(2,3));cv.create_oval(xx-2,yy-2,xx+2,yy+2,fill=GOLD,outline='')
        state='COMPLETE' if w.done else ('RUNNING' if self.running else 'PAUSED')
        self.stats.config(text=f'{state}  ·  {w.tick*DT:.1f}s  ·  Delivered {w.delivered}/{w.config.foods*w.config.food_units}  ·  Discovered {len(w.discovered)}/{w.config.foods}')
        self.inspect.config(text=f'Ant {self.selected+1}  |  {a.decision}\nDelivered by this ant: {a.delivered}   ·   Tick {w.tick}   ·   Seed {w.config.seed}')
        self.speed_label.config(text=f'Playback {self.speed.get():.1f}×')
        ch=self.chart;ch.delete('all');cw=max(80,ch.winfo_width());ch.create_text(12,13,anchor='w',text='FOOD DELIVERED / SIMULATED TIME',fill=MUTED,font=(FONT,9))
        data=w.history+[(w.tick,w.delivered)];maximum=w.config.foods*w.config.food_units
        points=[v for tick,value in data for v in (12+(cw-30)*tick/max(1,w.tick),77-48*value/maximum)]
        if len(points)>=4:ch.create_line(*points,fill=TEAL,width=2)
        ch.create_text(cw-12,13,anchor='e',text=str(w.delivered),fill=TEAL,font=(FONT,10,'bold'))

    def close(self):
        self.closed=True
        if self.after_id:self.after_cancel(self.after_id)
        self.pool.shutdown(wait=True,cancel_futures=True);self.destroy()
