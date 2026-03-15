/** Custom hook for task management */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/api';

export const useTasks = (params = {}) => {
  return useQuery({
    queryKey: ['tasks', params],
    queryFn: () => apiService.getTasks(params).then((res) => res.data),
    staleTime: 30000, // 30 seconds
  });
};

export const useTask = (id) => {
  return useQuery({
    queryKey: ['task', id],
    queryFn: () => apiService.getTask(id).then((res) => res.data),
    enabled: !!id,
  });
};

export const useCreateTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => apiService.createTask(data).then((res) => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useUpdateTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => apiService.updateTask(id, data).then((res) => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['task', variables.id] });
    },
  });
};

export const useDeleteTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => apiService.deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};

export const useToggleTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id) => apiService.toggleTask(id).then((res) => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
};
