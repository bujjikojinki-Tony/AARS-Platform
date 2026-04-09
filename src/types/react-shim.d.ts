declare namespace JSX {
  interface IntrinsicElements {
    [elementName: string]: any;
  }
}

declare module "react" {
  export function useState<T>(initialState: T): [T, (value: T) => void];
}

declare module "react/jsx-runtime" {
  export const Fragment: any;
  export function jsx(type: any, props: any, key?: any): any;
  export function jsxs(type: any, props: any, key?: any): any;
}
