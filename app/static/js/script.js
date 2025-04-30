document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('startButton');
    const videoContainer = document.getElementById('videoContainer');
    const satisfactionScoreElement = document.getElementById('satisfactionScore');
    
    let interval;
    
    startButton.addEventListener('click', () => {
        if (videoContainer.style.display === 'none' || videoContainer.style.display === '') {
            videoContainer.style.display = 'block';
            startButton.textContent = 'Stop Detection';
            interval = setInterval(updateSatisfactionScore, 1000);  // Update every second
        } else {
            videoContainer.style.display = 'none';
            startButton.textContent = 'Start Detection';
            clearInterval(interval);  // Stop polling when detection is stopped
        }
    });
    
    function updateSatisfactionScore() {
        fetch('/satisfaction_score')
            .then(response => response.json())
            .then(data => {
                satisfactionScoreElement.textContent = data.satisfaction_score.toFixed(2);
            })
            .catch(error => console.error('Error fetching satisfaction score:', error));
    }
});
