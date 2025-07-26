export declare class VercelAgent {
    private model;
    constructor(model: string);
    invoke(messages: {
        role: 'user' | 'assistant';
        content: string;
    }[]): Promise<string>;
    stream(messages: {
        role: 'user' | 'assistant';
        content: string;
    }[]): AsyncIterable<string> & ReadableStream<string>;
}
