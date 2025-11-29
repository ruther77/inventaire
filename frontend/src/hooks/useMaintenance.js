import { useQuery } from '@tanstack/react-query';
import api from '../api/client.js';

const fetchBackups = async (limit = 100) => {
  const { data } = await api.get('/maintenance/backups', { params: { limit } });
  return data.backups ?? [];
};

export function useBackups(limit) {
  return useQuery({
    queryKey: ['maintenance-backups', limit],
    queryFn: () => fetchBackups(limit),
    keepPreviousData: true,
  });
}
