declare namespace JSX {
  interface IntrinsicElements {
    [elementName: string]: any;
  }
}

declare namespace React {
  type ReactNode = any;
}

declare module "react" {
  export function useState<T>(initialState: T): [T, (value: T) => void];
  export function useMemo<T>(factory: () => T, deps: unknown[]): T;
  export function useEffect(effect: () => void | (() => void), deps?: unknown[]): void;
  export function useReducer<S, A>(
    reducer: (state: S | null, action: A) => S | null,
    initialState: S,
  ): [S | null, (value: A) => void];

  const React: {
    useState: typeof useState;
    useMemo: typeof useMemo;
    useEffect: typeof useEffect;
    useReducer: typeof useReducer;
    ReactNode: any;
  };

  export default React;
}

declare module "react/jsx-runtime" {
  export const Fragment: any;
  export function jsx(type: any, props: any, key?: any): any;
  export function jsxs(type: any, props: any, key?: any): any;
}
