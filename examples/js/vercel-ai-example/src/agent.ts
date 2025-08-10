import { openai } from '@ai-sdk/openai';
import { generateText, streamText, tool } from 'ai';
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

const checkInventoryTool = tool({
  description: "Get the inventory of a specific color and size of T-shirt",
  parameters: z.object({
    color: z.string().describe("Color of the t-shirt"),
    size: z.string().describe("Size of the t-shirt"),
  }),
  execute: async ({ color, size }) => {
    return `100 ${color} ${size} T-shirts in stock`
  },
})

const sendEmailTool = tool({
  description: "Send an email to a customer",
  parameters: z.object({
    email: z.string().describe("Email address of the recipient"),
    subject: z.string().describe("Email subject"),
    body: z.string().describe("Email body"),
  }),
  execute: async ({ email, subject, body }) => {
    return `Email sent to ${email} with subject ${subject} and body ${body}`
  },
})


export class VercelAgent {
  private model: string;

  constructor(model: string) {
    this.model = model;
  }

  public async invoke(messages: { role: 'user' | 'assistant', content: string }[]): Promise<string> {
    const response = await generateText({
      model: openai(this.model),
      system: agentInstructions,
      messages: messages,
      tools: {
        check_inventory: checkInventoryTool,
        send_email: sendEmailTool,
      },
    });
    return response.text;
  }

  public stream(messages: { role: 'user' | 'assistant', content: string }[]): AsyncIterable<string> & ReadableStream<string> {
    const { textStream } = streamText({
      model: openai(this.model),
      system: agentInstructions,
      messages: messages,
      tools: {
        check_inventory: checkInventoryTool,
        send_email: sendEmailTool,
      },
    });

    return textStream;
  }
}
