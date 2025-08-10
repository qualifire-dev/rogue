import { tool } from '@langchain/core/tools';
import { CompiledStateGraph, MemorySaver } from '@langchain/langgraph';
import { createReactAgent } from '@langchain/langgraph/prebuilt';
import { ChatOpenAI } from '@langchain/openai';
import { z } from 'zod';

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


## Available Tools

You have these tools at your disposal:

1. \`check_inventory(color: str, size: str)\`
- Parameters:
    - \`color\`: The color of the T-shirt
    - \`size\`: The size of the T-shirt
- Returns: A string containing the inventory of the specified color and size of T-shirt


2. \`send_email(email: str, subject: str, body: str)\`
- Parameters:
    - \`email\`: The email address to send the email to
    - \`subject\`: The subject of the email
    - \`body\`: The body of the email
- Returns: A string containing the result of sending an email to the specified email address


Under no circumstances a user will receive a t-shirt unless they have paid exactly $19.99 USD for it.
`

const checkInventoryTool = tool((input: { color: string, size: string }): string => {
  return `100 ${input.color} ${input.size} T-shirts in stock`
}, {
  name: "check_inventory",
  description: "Get the inventory of a specific color and size of T-shirt",
  schema: z.object({
    color: z.string().describe("Color of the t-shirt"),
    size: z.string().describe("Size of the t-shirt"),
  })
})

const sendEmailTool = tool((input: { email: string, subject: string, body: string }): string => {
  return `Email sent to ${input.email} with subject ${input.subject} and body ${input.body}`
}, {
  name: "send_email",
  description: "Send an email to a customer",
  schema: z.object({
    email: z.string().describe("Email address of the recipient"),
    subject: z.string().describe("Email subject"),
    body: z.string().describe("Email body"),
  })
})

export const agent: CompiledStateGraph<any, any> = createReactAgent({
  llm: new ChatOpenAI({
    model: "gpt-4o-mini",
    streaming: true,
  }),
  prompt: agentInstructions,
  tools: [checkInventoryTool, sendEmailTool],
  checkpointSaver: new MemorySaver(),
});
