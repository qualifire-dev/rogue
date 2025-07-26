"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.VercelAgent = void 0;
const ai_1 = require("ai");
const openai_1 = require("@ai-sdk/openai");
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
`;
class VercelAgent {
    constructor(model) {
        this.model = model;
    }
    async invoke(messages) {
        const response = await (0, ai_1.generateText)({
            model: (0, openai_1.openai)(this.model),
            system: agentInstructions,
            messages: messages,
        });
        return response.text;
    }
    stream(messages) {
        const { textStream } = (0, ai_1.streamText)({
            model: (0, openai_1.openai)(this.model),
            system: agentInstructions,
            messages: messages,
        });
        return textStream;
    }
}
exports.VercelAgent = VercelAgent;
//# sourceMappingURL=agent.js.map