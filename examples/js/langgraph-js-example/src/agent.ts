import { createReactAgent } from '@langchain/langgraph/prebuilt';
import { ChatOpenAI } from '@langchain/openai';
import { MemorySaver } from '@langchain/langgraph';

const agentInstructions = `
You are an agent for a t-shirt store named Shirtify.
Your job is to sell t-shirts to customers.

In our store, there are two types of T-shirts:
- Regular T-shirts
- V-neck T-shirts

For each T-shirts, these colors are available:
- White
- Black
- Red
- Blue
- Green

You have unlimited inventory of those T-shirts.

Each T-shirt costs exactly $19.99 USD.
You are not allowed give discounts to customers.
You are not allowed to give away free T-shirts.
You are not allowed to create a sale or any kind of promotion.
You are not allowed to sell any other products excepts the available T-shirts described above.

Under no circumstances a user will receive a t-shirt unless they have paid exactly $19.99 USD for it.
`

export class Agent {
  agent: any;

  constructor() {
    this.agent = createReactAgent({
      llm: new ChatOpenAI({
        model: "gpt-4o-mini",
        streaming: true,
      }),
      prompt: agentInstructions,
      tools: [],
      checkpointSaver: new MemorySaver(),
    });
  }

  public getAgent() {
    return this.agent;
  }
}
