/**
 * 文件管理 API 调用
 */

import axiosInstance from './axios';

/** 文件响应 */
export interface FileResponse {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  description: string | null;
  created_at: string;
  is_duplicate: boolean;
  user_id: number;
}

/** 文件列表响应 */
export interface FileListResponse {
  total: number;
  files: FileResponse[];
}

/**
 * 上传文件（仅 admin）
 */
export const uploadFile = async (
  file: File,
  description?: string
): Promise<FileResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (description) {
    formData.append('description', description);
  }

  const response = await axiosInstance.post<FileResponse>('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * 获取文件列表
 */
export const listFiles = async (): Promise<FileListResponse> => {
  const response = await axiosInstance.get<FileListResponse>('/files/files');
  return response.data;
};

/**
 * 删除文件（仅 admin）
 */
export const deleteFile = async (fileId: number): Promise<void> => {
  await axiosInstance.delete(`/files/files/${fileId}`);
};
