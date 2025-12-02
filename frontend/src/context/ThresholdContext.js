/**
 * Global Threshold Configuration Context.
 * Provides active threshold config to all components for health status determination.
 */
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { superAdminAPI } from '../services/api';
import { isAuthenticated } from '../utils/auth';

// Default thresholds (fallback if API fails)
const DEFAULT_THRESHOLDS = {
  systolic_min: 90,
  systolic_max: 120,
  diastolic_min: 60,
  diastolic_max: 90,
  heart_rate_min: 60,
  heart_rate_max: 90,
};

const ThresholdContext = createContext({
  thresholds: DEFAULT_THRESHOLDS,
  loading: false,
  refreshThresholds: () => {},
});

export const ThresholdProvider = ({ children }) => {
  const [thresholds, setThresholds] = useState(DEFAULT_THRESHOLDS);
  const [loading, setLoading] = useState(false);

  const fetchThresholds = useCallback(async () => {
    if (!isAuthenticated()) {
      return;
    }
    try {
      setLoading(true);
      const res = await superAdminAPI.getActiveThresholds();
      if (res.data && res.data.config) {
        setThresholds(res.data.config);
      }
    } catch (error) {
      console.error('Failed to fetch thresholds:', error);
      // Keep default thresholds on error
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch on mount and when user authenticates
  useEffect(() => {
    if (isAuthenticated()) {
      fetchThresholds();
    }
  }, [fetchThresholds]);

  // Utility function to classify a health record
  const classifyRecord = useCallback((systolic, diastolic, heartRate) => {
    const sysHealthy = systolic >= thresholds.systolic_min && systolic <= thresholds.systolic_max;
    const diaHealthy = diastolic >= thresholds.diastolic_min && diastolic <= thresholds.diastolic_max;
    const hrHealthy = heartRate === null || heartRate === undefined || (heartRate >= thresholds.heart_rate_min && heartRate <= thresholds.heart_rate_max);

    if (sysHealthy && diaHealthy && hrHealthy) {
      return 'healthy';
    }

    // Borderline check (within 20% margin of thresholds)
    const isBorderline = (val, min, max) => {
      const margin = (max - min) * 0.2;
      if (val < min) return val >= min - margin;
      if (val > max) return val <= max + margin;
      return true;
    };

    const sysBorder = isBorderline(systolic, thresholds.systolic_min, thresholds.systolic_max);
    const diaBorder = isBorderline(diastolic, thresholds.diastolic_min, thresholds.diastolic_max);
    const hrBorder = heartRate === null || heartRate === undefined || isBorderline(heartRate, thresholds.heart_rate_min, thresholds.heart_rate_max);

    if (sysBorder && diaBorder && hrBorder) {
      return 'borderline';
    }

    return 'abnormal';
  }, [thresholds]);

  return (
    <ThresholdContext.Provider value={{ thresholds, loading, refreshThresholds: fetchThresholds, classifyRecord }}>
      {children}
    </ThresholdContext.Provider>
  );
};

export const useThresholds = () => useContext(ThresholdContext);
