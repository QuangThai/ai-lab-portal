/** Shared motion tokens for public editorial pages */
export const publicEase = [0.16, 1, 0.3, 1] as const;

export const publicFadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.52, delay: i * 0.08, ease: publicEase },
  }),
};

export const publicFadeIn = {
  hidden: { opacity: 0, y: 12 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.48, ease: publicEase },
  },
};

export const publicStaggerContainer = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.09, delayChildren: 0.05 },
  },
};

export const publicStaggerItem = {
  hidden: { opacity: 0, y: 18 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.46, ease: publicEase },
  },
};
