// Delete Tour Confirm-specific JavaScript extracted from delete_tour_confirm.html
function confirmFinalDelete() {
    const confirmInput = document.getElementById('confirm-delete');
    if (confirmInput.value !== 'DELETE') {
        alert('Please type "DELETE" to confirm the deletion.');
        return false;
    }
    
    return confirm('Are you absolutely sure you want to delete this tour? This action cannot be undone.');
}
