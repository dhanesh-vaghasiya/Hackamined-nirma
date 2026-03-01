import { useState } from "react";

/**
 * Custom hook for form state management.
 * @param {object} initialValues - Initial form values
 */
const useForm = (initialValues = {}) => {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setValues((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
    // Clear error on change
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const reset = () => {
    setValues(initialValues);
    setErrors({});
  };

  const setFieldValue = (name, value) => {
    setValues((prev) => ({ ...prev, [name]: value }));
  };

  const setFieldError = (name, error) => {
    setErrors((prev) => ({ ...prev, [name]: error }));
  };

  return {
    values,
    errors,
    handleChange,
    reset,
    setFieldValue,
    setFieldError,
    setValues,
    setErrors,
  };
};

export default useForm;
