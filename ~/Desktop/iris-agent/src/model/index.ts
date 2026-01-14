/**
 * Model provider interface and stub implementation
 */

export interface ModelProvider {
  generate(prompt: string, context?: Record<string, any>): Promise<string>;
  supportsStreaming(): boolean;
}

export interface ModelResponse {
  text: string;
  usage?: {
    inputTokens: number;
    outputTokens: number;
  };
}

/**
 * Stub model provider for testing/dummy responses
 */
export class DummyProvider implements ModelProvider {
  async generate(prompt: string, context?: Record<string, any>): Promise<string> {
    // Simple rule-based responses for testing
    if (prompt.includes('READ') || prompt.includes('read')) {
      return 'I need to read the following files: src/engine.ts, src/task.ts';
    }

    if (prompt.includes('PLAN') || prompt.includes('plan')) {
      return 'I plan to edit src/engine.ts lines 88-142 to implement the new feature.';
    }

    if (prompt.includes('WRITE') || prompt.includes('write')) {
      return 'Apply the following changes:\n- Add import statement\n- Modify function signature\n- Update logic';
    }

    return 'Task completed successfully.';
  }

  supportsStreaming(): boolean {
    return false;
  }
}

/**
 * OpenAI provider (stub - requires API key)
 */
export class OpenAIProvider implements ModelProvider {
  private apiKey?: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey || process.env.OPENAI_API_KEY;
  }

  async generate(prompt: string, context?: Record<string, any>): Promise<string> {
    if (!this.apiKey) {
      throw new Error('OpenAI API key not configured');
    }

    // TODO: Implement actual OpenAI API call
    return 'OpenAI response placeholder';
  }

  supportsStreaming(): boolean {
    return true;
  }
}

/**
 * Model router for provider selection
 */
export class ModelRouter {
  private providers: Map<string, ModelProvider> = new Map();
  private defaultProvider = 'dummy';

  constructor() {
    // Register built-in providers
    this.providers.set('dummy', new DummyProvider());
    this.providers.set('openai', new OpenAIProvider());
  }

  registerProvider(name: string, provider: ModelProvider): void {
    this.providers.set(name, provider);
  }

  async generate(prompt: string, context?: Record<string, any>, provider?: string): Promise<string> {
    const p = this.providers.get(provider || this.defaultProvider);
    if (!p) {
      throw new Error(`Provider ${provider} not found`);
    }
    return p.generate(prompt, context);
  }

  getProvider(name: string): ModelProvider | undefined {
    return this.providers.get(name);
  }

  listProviders(): string[] {
    return Array.from(this.providers.keys());
  }
}

// Global model router instance
export const modelRouter = new ModelRouter();