import mesa

class MyAgent(mesa.Agent):
    def __init__(self, model, age):
        super().__init__(model)
        self.age = age

    def step(self):
        self.age += 1
        print(f"Agent {self.unique_id} now is {self.age} years old")
        # Whatever else the agent does when activated

class MyModel(mesa.Model):
    def __init__(self, n_agents):
        super().__init__()
        self.grid = mesa.discrete_space.OrthogonalMooreGrid((10, 10), torus=True)
        initial_ages = self.rng.integers(0, 80, size=n_agents)
        # Crear agentes (la queue)
        agents = MyAgent.create_agents(self, n_agents, initial_ages)
        for agent in agents:
            agent.cell = self.grid.all_cells.select_random_cell() # type: ignore

    def step(self):
        # Va generando un agente en el orden que se crearon en la queue (manual)
        self.agents.do("step")

model = MyModel(n_agents=5)
model.run_for(1)