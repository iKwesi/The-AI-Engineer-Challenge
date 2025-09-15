import '@testing-library/jest-dom';

// Polyfill for HTMLFormElement.prototype.requestSubmit
if (!HTMLFormElement.prototype.requestSubmit) {
  HTMLFormElement.prototype.requestSubmit = function(submitter) {
    if (submitter) {
      const event = new Event('submit', { bubbles: true, cancelable: true });
      Object.defineProperty(event, 'submitter', { value: submitter });
      this.dispatchEvent(event);
    } else {
      this.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    }
  };
}
