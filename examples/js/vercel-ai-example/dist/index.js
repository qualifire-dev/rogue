"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const server_1 = require("@a2a-js/sdk/server");
const agentExecutor_js_1 = require("./agentExecutor.js");
const express_1 = __importDefault(require("express"));
const agent_js_1 = require("./agent.js");
function getAgentCard() {
    const skills = [
        {
            id: 'sell_tshirt',
            name: 'Sell T-Shirt',
            description: 'Helps with selling T-Shirts',
            tags: ['sell'],
        },
    ];
    const host = process.env.HOST || 'localhost';
    const port = process.env.PORT || 3000;
    return {
        name: 'Shirtify TShirt Store Agent',
        description: 'Sells Shirtify T-Shirts',
        url: `http://${host}:${port}/`,
        version: '1.0.0',
        defaultInputModes: ['text'],
        defaultOutputModes: ['text'],
        capabilities: { streaming: true },
        skills,
    };
}
async function main() {
    const taskStore = new server_1.InMemoryTaskStore();
    const agent = new agent_js_1.VercelAgent('gpt-4o-mini');
    const agentExecutor = new agentExecutor_js_1.VercelAgentExecutor(agent);
    // 3. Create DefaultRequestHandler
    const requestHandler = new server_1.DefaultRequestHandler(getAgentCard(), taskStore, agentExecutor);
    // 4. Create and setup A2AExpressApp
    const app = (0, express_1.default)();
    const appBuilder = new server_1.A2AExpressApp(requestHandler);
    // Use type assertion to work around Express type incompatibility
    const expressApp = appBuilder.setupRoutes(app);
    // 5. Start the server
    const PORT = process.env.PORT || 3000;
    const server = expressApp.listen(PORT, () => {
        console.log(`[ReactAgent] Server using langchain framework and A2A started on http://localhost:${PORT}`);
        console.log(`[ReactAgent] Agent Card: http://localhost:${PORT}/.well-known/agent.json`);
        console.log('[ReactAgent] Press Ctrl+C to stop the server');
    });
    // 6. Setup graceful shutdown
    const shutdown = async () => {
        console.log('\n[ReactAgent] Shutting down server...');
        // Close the HTTP server
        server.close(() => {
            console.log('[ReactAgent] HTTP server closed');
        });
        process.exit(0);
    };
    // Handle termination signals
    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
}
// Call the main function to start the server
main().catch(error => {
    console.error('Error starting server:', error);
    process.exit(1);
});
//# sourceMappingURL=index.js.map