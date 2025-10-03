// Landing Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const planForm = document.getElementById('plan-form');
    const generateButton = document.getElementById('generate-button');
    const resultsContainer = document.getElementById('results-container');
    const planOutput = document.getElementById('plan-output');
    const loginPrompt = document.getElementById('login-prompt');

    if (!planForm) return;

    planForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        generateButton.textContent = 'Generating...';
        generateButton.disabled = true;
        resultsContainer.classList.remove('hidden');
        planOutput.innerHTML = '<p class="loading"><i class="fas fa-spinner fa-spin"></i> Your personal AI agronomist is analyzing local data...</p>';
        loginPrompt.classList.add('hidden');

        const formData = new FormData(planForm);
        const data = {
            location: formData.get('location'),
            space: formData.get('space'),
            budget: formData.get('budget'),
            country: formData.get('country'),
            currency: formData.get('currency'),
        };

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                const errorHtml = result.error.includes('<p') ? result.error : `<p class="error-message">${result.error}</p>`;
                planOutput.innerHTML = errorHtml;
            } else {
                planOutput.innerHTML = result.plan;
                loginPrompt.classList.remove('hidden');
            }
        } catch (error) {
            planOutput.innerHTML = `<p class="error-message">A network error occurred. Please try again.</p>`;
        } finally {
            generateButton.textContent = 'Generate My Free Plan';
            generateButton.disabled = false;
        }
    });
});
