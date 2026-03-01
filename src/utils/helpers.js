/**
 * Format a date string into a readable format.
 * @param {string|Date} date
 * @param {object} options - Intl.DateTimeFormat options
 */
export const formatDate = (date, options = {}) => {
  const defaultOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
    ...options,
  };
  return new Intl.DateTimeFormat("en-US", defaultOptions).format(
    new Date(date)
  );
};

/**
 * Truncate a string to a max length.
 */
export const truncate = (str, maxLen = 100) => {
  if (!str || str.length <= maxLen) return str;
  return str.slice(0, maxLen) + "...";
};

/**
 * Capitalize first letter of a string.
 */
export const capitalize = (str) => {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
};

/**
 * Delay execution (useful for debounce/throttle).
 */
export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Simple classname merger (like clsx).
 */
export const cn = (...classes) => classes.filter(Boolean).join(" ");
