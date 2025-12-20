/**
 * PDF Components - Export central
 *
 * Tous les composants liés à l'affichage et la manipulation de PDF
 */

export { default as PDFPreview } from '../ui/PDFPreview.jsx';
export { default as PDFPreviewAdvanced } from '../ui/PDFPreviewAdvanced.jsx';
export { default as PDFViewerWrapper, useHighlights } from './PDFViewerWrapper.jsx';

// Re-export des hooks
export { usePDFFile, usePDFFileFromUpload } from '../../hooks/usePDFFile.js';
