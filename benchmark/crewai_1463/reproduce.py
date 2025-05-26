from crewai.flow.flow import Flow, and_, listen, start
import asyncio


class DummyFlow(Flow):
    @start()
    def step_1_1(self):
        print("Starting 'step_1_1' method.")

    @start()
    def step_1_2(self):
        print("Starting 'step_1_2' method.")

    @listen(step_1_1)
    def step_2(self):
        print("Starting 'step_2' method.")

    @listen(step_2)
    def step_3(self):
        print("Starting 'step_3' method.")
        print("Continue to step 4 ...")
        print("If it stops here, it is a bug...")

    @listen(and_(step_1_1, step_3))
    def step_4_1(self):
        print("Starting 'step_4_1' method.")

    @listen(and_("step_1_1", "step_3"))
    def step_4_2(self):
        print("Starting 'step_4_2' method.")
        print("✅ Completed")


async def main():
    podcast_flow = DummyFlow()
    await podcast_flow.kickoff()


asyncio.run(main())