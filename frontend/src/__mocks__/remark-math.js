// Mock for remark-math
const remarkMath = () => {
  return (tree) => {
    // Simple mock that doesn't transform anything
    return tree;
  };
};

export default remarkMath;
