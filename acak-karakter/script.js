document.getElementById('generate').addEventListener('click', generateRandomStrings);
document.getElementById('copyAll').addEventListener('click', copyAllResults);

function generateRandomStrings() {
    const uppercase = document.getElementById('uppercase').value;
    const lowercase = document.getElementById('lowercase').value;
    const numbers = document.getElementById('numbers').value;
    const symbols = document.getElementById('symbols').value;

    const allChars = (uppercase + lowercase + numbers + symbols).split('');
    const uniqueChars = [...new Set(allChars)];

    if (uniqueChars.length < 10) {
        alert('Total karakter unik harus minimal 10. Saat ini: ' + uniqueChars.length);
        return;
    }

    const results = [];
    for (let i = 0; i < 10; i++) {
        const shuffled = shuffleArray([...uniqueChars]);
        const randomString = shuffled.slice(0, 10).join('');
        results.push(randomString);
    }

    displayResults(results);
}

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

function displayResults(results) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';

    results.forEach((result, index) => {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item';

        const span = document.createElement('span');
        span.textContent = result;

        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.textContent = 'Salin';
        copyBtn.addEventListener('click', () => copyToClipboard(result));

        resultItem.appendChild(span);
        resultItem.appendChild(copyBtn);
        resultsDiv.appendChild(resultItem);
    });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Teks berhasil disalin!');
    }).catch(err => {
        console.error('Gagal menyalin teks: ', err);
    });
}

function copyAllResults() {
    const results = document.querySelectorAll('.result-item span');
    const allText = Array.from(results).map(span => span.textContent).join('\n');
    copyToClipboard(allText);
}
