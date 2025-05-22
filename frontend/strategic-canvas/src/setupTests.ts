import '@testing-library/jest-dom';

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock HTMLElement methods that ReactFlow uses
Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
  configurable: true,
  value: 500,
});

Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
  configurable: true,
  value: 800,
});

// Mock getBoundingClientRect
HTMLElement.prototype.getBoundingClientRect = jest.fn(() => ({
  width: 800,
  height: 500,
  top: 0,
  left: 0,
  bottom: 500,
  right: 800,
  x: 0,
  y: 0,
  toJSON: jest.fn(),
}));

// Mock DOMRect
global.DOMRect = {
  fromRect: () => ({
    top: 0,
    left: 0,
    bottom: 500,
    right: 800,
    width: 800,
    height: 500,
    x: 0,
    y: 0,
    toJSON: jest.fn(),
  }),
} as any;

// Mock pointerCapture methods
HTMLElement.prototype.setPointerCapture = jest.fn();
HTMLElement.prototype.releasePointerCapture = jest.fn();
HTMLElement.prototype.hasPointerCapture = jest.fn();

// Mock for MUI TouchRipple
Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
  configurable: true,
  value: 800,
});

Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
  configurable: true,
  value: 500,
});

// Mock Touch and TouchList for touch events
global.Touch = class Touch {
  constructor(touchInit: TouchInit) {
    Object.assign(this, touchInit);
  }
} as any;

global.TouchList = class TouchList {
  length = 0;
  constructor(touches: Touch[] = []) {
    touches.forEach((touch, index) => {
      this[index] = touch;
    });
    this.length = touches.length;
  }
  item(index: number) {
    return this[index] || null;
  }
} as any;