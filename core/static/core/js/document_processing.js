// Document Processing-specific JavaScript extracted from document_processing.html
// Real-time processing status updates
function startProcessing(documentId) {
    // This function is no longer needed since we let the link work normally
    // The processing status will be handled by the server redirect
}

function pollProcessingStatus(documentId) {
    const pollInterval = setInterval(() => {
        fetch(`/documents/${documentId}/status/`)
            .then(response => response.json())
            .then(data => {
                if (data.is_completed) {
                    clearInterval(pollInterval);
                    location.reload(); // Reload to show results
                } else if (data.is_failed) {
                    clearInterval(pollInterval);
                    location.reload(); // Reload to show error
                }
                // Continue polling if still processing
            })
            .catch(error => {
                console.error('Error polling status:', error);
                // Continue polling even if there's an error
            });
    }, 2000); // Poll every 2 seconds
    
    // Stop polling after 2 minutes (120 seconds) to prevent infinite polling
    setTimeout(() => {
        clearInterval(pollInterval);
    }, 120000);
}

// Auto-start polling for any documents currently processing
document.addEventListener('DOMContentLoaded', function() {
    const processingDocuments = document.querySelectorAll('.processing-indicator');
    processingDocuments.forEach(indicator => {
        const documentId = indicator.closest('.action-buttons').getAttribute('data-document-id');
        if (documentId) {
            pollProcessingStatus(documentId);
        }
    });
});
