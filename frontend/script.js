document.getElementById('itemForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const item = document.getElementById('item').value;
    const responseDiv = document.getElementById('response');

    try {
        const response = await fetch('http://localhost:80/items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ item })
        });

        const data = await response.json();
        responseDiv.style.display = 'block';
        responseDiv.innerHTML = `<strong>Status:</strong> ${data.status}<br><strong>Item:</strong> ${data.item}`;
    } catch (error) {
        responseDiv.style.display = 'block';
        responseDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
    }
});