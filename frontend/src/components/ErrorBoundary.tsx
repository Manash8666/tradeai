import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 rounded-2xl border border-rose-500/30 bg-rose-950/20 backdrop-blur-xl text-center flex flex-col items-center justify-center my-4">
          <AlertTriangle className="w-10 h-10 text-rose-400 mb-2" />
          <h3 className="text-base font-bold text-white font-syne">
            {this.props.fallbackTitle || 'Component Encountered a Transient Error'}
          </h3>
          <p className="text-xs text-rose-300 font-mono mt-1 max-w-md">
            {this.state.error?.message || 'Unknown error occurred'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-4 px-4 py-2 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-xs font-mono text-white flex items-center gap-2 cursor-pointer transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry Component
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
