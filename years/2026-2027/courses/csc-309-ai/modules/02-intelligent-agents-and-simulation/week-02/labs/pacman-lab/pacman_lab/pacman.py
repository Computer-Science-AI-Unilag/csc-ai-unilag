"""Public constructor/factories. Rendering is imported only by play()."""
from .core import Game, Scoring
from .worlds import fixed_world, random_world, random_positions, SPECIALS

class Pacman:
    def __init__(self, gridWorld=None, foodPositions=None, agentPosition=None, *,
                 width=21, height=15, food_count=4, seed=42,
                 start_score=50, step_cost=1, food_reward=50, tick_ms=250):
        if type(tick_ms) is not int or not 40 <= tick_ms <= 5000:
            raise ValueError('tick_ms must be an integer from 40 to 5000.')
        generated = gridWorld is None
        grid = random_world(width,height,seed) if generated else gridWorld
        # Omitted positions on a random world are generated; on an explicit world
        # an omitted/invalid agent stays hidden, as in the configuration editor.
        if generated:
            start,foods = random_positions(grid,food_count,seed,agentPosition)
            agentPosition = start
            if foodPositions is None:
                foodPositions = foods
        self.scoring = Scoring(start_score,step_cost,food_reward)
        game = Game(grid,foodPositions or [],agentPosition,self.scoring)
        self.config = game.raw()
        # Preserve original food/start so time-zero pickup is repeatable on reset.
        self.config['foods'] = [list(p) for p in sorted(set(map(tuple,foodPositions or []))) if
                                0 <= p[0] < len(game.grid) and 0 <= p[1] < len(game.grid[0]) and game.grid[p[0]][p[1]]]
        self.warnings = game.warnings
        self.tick_ms = tick_ms
        self.title = 'Custom maze' if not generated else f'Random maze / seed {seed}'

    def new_game(self):
        return Game(self.config['grid'],self.config['foods'],self.config['agent'],self.scoring)

    @classmethod
    def special(cls, number=1, **kwargs):
        if number not in SPECIALS:
            raise ValueError('Special lesson must be 1 through 6.')
        title,world,start,foods = SPECIALS[number]
        result = cls(fixed_world(world),foods,start,**kwargs)
        result.title = title
        return result

    @classmethod
    def world(cls, number=1, food_count=4, seed=42, **kwargs):
        grid = fixed_world(number)
        start,foods = random_positions(grid,food_count,seed)
        result = cls(grid,foods,start,**kwargs)
        result.title = f'Fixed world {number}'
        return result

    def play(self, agent=None):
        from .ui import ClassroomApp
        ClassroomApp(self,agent).mainloop()

    def run(self, agent, max_steps=10000):
        """Non-visual evaluation. No wall-clock penalties while agents calculate."""
        game = self.new_game()
        if game.status != 'ready':
            return game
        if hasattr(agent,'cancel'):
            agent.cancel.clear()
        agent.init(game.position,sorted(game.foods),[r[:] for r in game.grid])
        while game.status in ('ready','running') and game.tick < max_steps:
            action = agent.nextAction(game.position,sorted(game.foods))
            game.step(action)
        if game.status in ('ready','running'):
            game.status = 'step_limit'
        return game
