import { useState, useEffect } from 'react';
import { checkHealth } from '../services/api';

export const useHealthCheck = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const performCheck = async () => {
    setLoading(true);
    try {
      const res = await checkHealth();
      setData(res);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    performCheck();
  }, []);

  return { data, loading, error, refetch: performCheck };
};
