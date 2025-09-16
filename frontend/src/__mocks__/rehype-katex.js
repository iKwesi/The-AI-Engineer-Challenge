// Mock for rehype-katex
const rehypeKatex = () => {
  return (tree) => {
    // Simple mock that doesn't transform anything
    return tree;
  };
};

export default rehypeKatex;
