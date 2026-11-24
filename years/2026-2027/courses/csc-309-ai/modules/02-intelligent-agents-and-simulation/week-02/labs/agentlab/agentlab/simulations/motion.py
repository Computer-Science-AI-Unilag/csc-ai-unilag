"""Wall-aware straight-line forecasts. No hypothetical particle impulses."""
from dataclasses import dataclass
import math
from agentlab.core.vector import Vec2


@dataclass(frozen=True, slots=True)
class Segment:
    start: float
    end: float
    position: Vec2
    velocity: Vec2


def rotate(v: Vec2, degrees: float) -> Vec2:
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    return Vec2(c*v.x-s*v.y, s*v.x+c*v.y)


def trace(boundary, p: Vec2, v: Vec2, radius: float, duration: float):
    """Return piecewise-linear path, final position/velocity, and wall impact count."""
    segments = []
    elapsed = 0.0
    hits = 0
    while elapsed < duration - 1e-14:
        remaining = duration-elapsed
        hit = remaining + 1
        normals = []
        if boundary.shape == 'circle':
            q = p-Vec2(.5,.5)
            aa = v.dot(v)
            if aa > 1e-20:
                b = q.dot(v)
                cc = q.dot(q)-(.44-radius)**2
                hit = max(0.0, (-b+math.sqrt(max(0.0,b*b-aa*cc)))/aa)
                at = p+v*hit
                normals = [(Vec2(.5,.5)-at).unit()]
        else:
            for anchor,n in boundary.planes:
                vn = v.dot(n)
                if vn < -1e-14:
                    t = max(0.0, ((p-anchor).dot(n)-radius)/(-vn))
                    if t < hit-1e-12:
                        hit,normals = t,[n]
                    elif abs(t-hit)<1e-12:
                        normals.append(n)
        travel = min(remaining, hit)
        if travel > 1e-14:
            segments.append(Segment(elapsed,elapsed+travel,p,v))
            p = p+v*travel
            elapsed += travel
        if hit > remaining:
            break
        for n in normals:
            vn = v.dot(n)
            if vn < 0:
                v = v-n*(2*vn)
                hits += 1
            p = p+n*1e-11
        if not normals:
            break
        if hits > 10000:
            raise ValueError('Motion exceeds the supported wall-reflection workload.')
    return segments,p,v,hits


def encounter(path_a, path_b, radius_sum: float, horizon: float):
    """Earliest contact time and minimum surface clearance, including between endpoints."""
    i=j=0
    first=math.inf
    clearance=math.inf
    while i<len(path_a) and j<len(path_b):
        a,b=path_a[i],path_b[j]
        lo,hi=max(a.start,b.start),min(a.end,b.end)
        if hi>=lo:
            p=(b.position+b.velocity*(lo-b.start))-(a.position+a.velocity*(lo-a.start))
            v=b.velocity-a.velocity
            span=hi-lo
            aa=v.dot(v)
            pv=p.dot(v)
            t=max(0.0,min(span,-pv/aa)) if aa>1e-20 else 0.0
            clearance=min(clearance,(p+v*t).length()-radius_sum)
            cc=p.dot(p)-radius_sum**2
            if cc<=1e-14:
                first=min(first,lo)
            elif aa>1e-20:
                disc=pv*pv-aa*cc
                if disc>=0:
                    entry=(-pv-math.sqrt(disc))/aa
                    if -1e-12<=entry<=span+1e-12:
                        first=min(first,lo+max(0,entry))
        if a.end<=b.end+1e-14:i+=1
        if b.end<=a.end+1e-14:j+=1
    return first,clearance
