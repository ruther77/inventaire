/**
 * usePDFFile - Hook pour gérer l'état du fichier PDF
 *
 * Fonctionnalités:
 * - Stockage du fichier PDF uploadé
 * - Génération d'URL blob
 * - Cleanup automatique
 * - Métadonnées (nom, taille, etc.)
 */

import { useState, useEffect, useCallback } from 'react';

export function usePDFFile() {
  const [file, setFile] = useState(null);
  const [fileUrl, setFileUrl] = useState(null);
  const [fileMetadata, setFileMetadata] = useState(null);

  // Cleanup de l'URL blob lors du changement de fichier
  useEffect(() => {
    if (!file) {
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
      setFileUrl(null);
      setFileMetadata(null);
      return;
    }

    // Si c'est un File/Blob, créer l'URL
    if (file instanceof File || file instanceof Blob) {
      const url = URL.createObjectURL(file);
      setFileUrl(url);

      // Extraire les métadonnées
      setFileMetadata({
        name: file.name || 'document.pdf',
        size: file.size,
        type: file.type,
        lastModified: file.lastModified ? new Date(file.lastModified) : null,
      });

      // Cleanup
      return () => {
        URL.revokeObjectURL(url);
      };
    }

    // Si c'est déjà une URL
    if (typeof file === 'string') {
      setFileUrl(file);
      setFileMetadata({
        name: 'document.pdf',
        size: null,
        type: 'application/pdf',
        lastModified: null,
      });
    }
  }, [file]);

  // Setter avec validation
  const setPDFFile = useCallback((newFile) => {
    if (!newFile) {
      setFile(null);
      return;
    }

    // Validation du type
    if (newFile instanceof File || newFile instanceof Blob) {
      const isPDF = newFile.type === 'application/pdf' || newFile.name?.endsWith('.pdf');
      if (!isPDF) {
        console.warn('Le fichier fourni n\'est pas un PDF');
      }
    }

    setFile(newFile);
  }, []);

  // Clear
  const clearPDFFile = useCallback(() => {
    setFile(null);
  }, []);

  // Formater la taille du fichier
  const formatFileSize = useCallback((bytes) => {
    if (!bytes) return 'N/A';
    const kb = bytes / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    const mb = kb / 1024;
    return `${mb.toFixed(1)} MB`;
  }, []);

  return {
    file,
    fileUrl,
    fileMetadata,
    setPDFFile,
    clearPDFFile,
    formatFileSize,
    hasFile: !!file,
  };
}

/**
 * usePDFFileFromUpload - Hook optimisé pour l'upload de factures
 * Combine usePDFFile avec la gestion de l'extraction
 */
export function usePDFFileFromUpload() {
  const pdfFile = usePDFFile();
  const [extractionData, setExtractionData] = useState(null);

  // Stocker à la fois le fichier ET les données extraites
  const handleFileExtracted = useCallback((file, data) => {
    pdfFile.setPDFFile(file);
    setExtractionData(data);
  }, [pdfFile]);

  // Clear tout
  const clearAll = useCallback(() => {
    pdfFile.clearPDFFile();
    setExtractionData(null);
  }, [pdfFile]);

  return {
    ...pdfFile,
    extractionData,
    setExtractionData,
    handleFileExtracted,
    clearAll,
  };
}
