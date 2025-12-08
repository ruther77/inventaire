import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchFinanceImports, importFinanceBankStatements } from '../api/client';

export const useFinanceImports = () =>
  useQuery({
    queryKey: ['finance', 'imports'],
    queryFn: () => fetchFinanceImports(),
  });

export const useFinanceImportMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ accountId, file }) => importFinanceBankStatements({ accountId, file }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finance', 'imports'] });
      queryClient.invalidateQueries({ queryKey: ['finance', 'transactions'] });
    },
  });
};
