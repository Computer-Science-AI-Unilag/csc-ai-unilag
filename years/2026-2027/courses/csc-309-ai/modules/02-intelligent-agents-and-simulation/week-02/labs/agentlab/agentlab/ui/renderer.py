"""Canvas projection only. Resizing never changes the physics world."""
import tkinter as tk
import sys

FONT = "Segoe UI" if sys.platform == "win32" else "Helvetica"
from agentlab.core.vector import Vec2

BG = '#090f1b'


class WorldRenderer:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.scale = 1.0
        self.ox = self.oy = 0.0

    def point(self, p: Vec2):
        return self.ox + p.x * self.scale, self.oy + p.y * self.scale

    def world_point(self, x, y):
        return Vec2((x - self.ox) / self.scale, (y - self.oy) / self.scale)

    def draw(self, sim, selected, trails=True, vectors=False, labels=False, settings=None, inspection=None, sensor_overlay=False, predictions=False):
        c = self.canvas
        width, height = c.winfo_width(), c.winfo_height()
        vertices=sim.boundary.vertices
        if vertices:
            xmin,xmax=min(p.x for p in vertices),max(p.x for p in vertices)
            ymin,ymax=min(p.y for p in vertices),max(p.y for p in vertices)
        else:
            xmin,ymin,xmax,ymax=.06,.06,.94,.94
        self.scale=max(1,min((width-36)/(xmax-xmin),(height-36)/(ymax-ymin)))
        self.ox=(width-(xmax-xmin)*self.scale)/2-xmin*self.scale
        self.oy=(height-(ymax-ymin)*self.scale)/2-ymin*self.scale
        c.delete('all')
        # Restrained dotted grid on the dark workspace.
        for x in range(24, width, 28):
            for y in range(24, height, 28):
                c.create_oval(x, y, x+1, y+1, fill='#1a2638', outline='')
        boundary = sim.boundary
        if boundary.shape == 'circle':
            x1,y1 = self.point(Vec2(.06,.06));x2,y2 = self.point(Vec2(.94,.94))
            c.create_oval(x1,y1,x2,y2,fill='#101c2c',outline='#233e50',width=8)
            c.create_oval(x1,y1,x2,y2,outline='#4fa6af',width=2)
        else:
            xy = [v for p in boundary.vertices for v in self.point(p)]
            c.create_polygon(*xy,fill='#101c2c',outline='#233e50',width=8,joinstyle=tk.ROUND)
            c.create_polygon(*xy,fill='',outline='#4fa6af',width=2,joinstyle=tk.ROUND)
        focus=next((b for b in sim.balls if b.id==selected),None)
        details=(inspection or {}).get(selected,{})
        if focus and settings and settings.sensing and settings.policy!='passive':
            x,y=self.point(focus.position)
            if sensor_overlay:
                rr=settings.sensing_radius*self.scale
                c.create_oval(x-rr,y-rr,x+rr,y+rr,outline='#346f82',dash=(5,5),width=1)
                for b in sim.balls:
                    if b.id in details.get('neighbours',[]):
                        bx,by=self.point(b.position)
                        c.create_line(x,y,bx,by,fill='#703d4c' if b.id in details.get('threats',[]) else '#234455',dash=(2,4))
            if predictions:
                from agentlab.simulations.motion import trace
                horizon=1 if settings.policy.startswith('reactive') else settings.horizon
                path,_,_,_=trace(sim.boundary,focus.position,focus.velocity,focus.radius,horizon/240)
                for segment in path:
                    a=self.point(segment.position)
                    b=self.point(segment.position+segment.velocity*(segment.end-segment.start))
                    c.create_line(*a,*b,fill='#ffe49a',width=3,dash=(3,3))
        collision_ids={i for pair in sim.first_collision_pairs for i in pair}
        for ball in sim.balls:
            if trails and len(ball.trail)>1:
                xy = [v for p in ball.trail for v in self.point(p)]
                c.create_line(*xy,fill='#354960',width=2,smooth=True)
            x,y=self.point(ball.position);r=ball.radius*self.scale
            if ball.id in collision_ids:
                c.create_oval(x-r-5,y-r-5,x+r+5,y+r+5,outline='#ff5f80',width=3)
            if ball.id == selected:
                c.create_oval(x-r-7,y-r-7,x+r+7,y+r+7,outline='#f3fafc',width=1,dash=(3,3))
            if sim.time - ball.event_time < .10:
                c.create_oval(x-r-4,y-r-4,x+r+4,y+r+4,outline=ball.color,width=1)
            c.create_oval(x-r,y-r,x+r,y+r,fill=ball.color,outline='')
            c.create_oval(x-r*.48,y-r*.58,x-r*.05,y-r*.15,fill='#e9fffd',outline='')
            if vectors:
                end = ball.position + ball.velocity * .18
                ex,ey=self.point(end)
                c.create_line(x,y,ex,ey,fill=ball.color,width=2,arrow=tk.LAST)
            if labels:
                c.create_text(x,y-r-11,text=str(ball.id),fill='#cedce8',font=(FONT,8))
