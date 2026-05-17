let ws = null;
let analysisData = [];
let sentimentChart = null;

// just some rough comments from me while testing, nothing special.

function normalizeSentiment(value) {
    if (typeof value === "number") {
        if (value > 0.1) return "positive";
        if (value < -0.1) return "negative";
        return "neutral";
    }

    if (typeof value === "string") {
        return value.toLowerCase();
    }

    return "neutral";
}

function sentimentToValue(value) {
    const sentiment = normalizeSentiment(value);
    if (sentiment === "positive") return 1;
    if (sentiment === "negative") return -1;
    return 0;
}

function setHidden(id, hidden) {
    const element = document.getElementById(id);
    if (!element) return;
    element.classList.toggle("hidden", hidden);
}

function setVisible(id, visible) {
    setHidden(id, !visible);
}

function cleanText(value) {
    return String(value ?? "")
        .replace(/[\u0000-\u001F\u007F]/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = function(event) {
        console.log("WebSocket connected");
    };

    ws.onmessage = function(event) {
        const message = event.data;
        appendCLILog(message);

        try {
            const data = JSON.parse(message);
            if (data.type === "results") {
                analysisData = data.data;
                displayAnalytics();
            }
        } catch (e) {
            // if it is not json, it is just a log line
        }
    };

    ws.onerror = function(event) {
        console.error("WebSocket error:", event);
        appendCLILog("ERROR: WebSocket connection failed", "error");
    };

    ws.onclose = function(event) {
        console.log("WebSocket closed");
        setTimeout(connectWebSocket, 3000);
    };
}

function appendCLILog(message, type = "info") {
    const cliOutput = document.getElementById("cliOutput");
    const line = document.createElement("div");
    line.className = "border border-stone-200 bg-stone-50 px-3 py-2 text-stone-700";
    
    if (message.includes("ERROR")) {
        line.className = "border border-red-200 bg-red-50 px-3 py-2 text-red-700";
    } else if (message.includes("WARNING")) {
        line.className = "border border-amber-200 bg-amber-50 px-3 py-2 text-amber-700";
    } else {
        line.className = "border border-stone-200 bg-stone-50 px-3 py-2 text-stone-700";
    }
    
    line.textContent = cleanText(message);
    cliOutput.appendChild(line);
    cliOutput.scrollTop = cliOutput.scrollHeight;
}

function startAnalysis() {
    const keyword = document.getElementById("keyword").value.trim();
    const numArticles = parseInt(document.getElementById("numArticles").value);

    if (!keyword) {
        alert("Please enter a keyword");
        return;
    }

    analysisData = [];
    document.getElementById("cliOutput").innerHTML = "";
    setVisible("loading", true);
    setHidden("analyticsGrid", true);
    setHidden("resultsTable", true);
    setHidden("emptyState", true);
    document.getElementById("analyzeBtn").disabled = true;

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            keyword: keyword,
            num_articles: numArticles
        }));
    }

}

function getSentimentClass(score) {
    const sentiment = normalizeSentiment(score);
    if (sentiment === "positive") return "border border-emerald-300 bg-emerald-50 text-emerald-800";
    if (sentiment === "negative") return "border border-red-300 bg-red-50 text-red-800";
    return "border border-stone-300 bg-stone-100 text-stone-700";
}

function getSentimentLabel(score) {
    const sentiment = normalizeSentiment(score);
    if (sentiment === "positive") return "Positive";
    if (sentiment === "negative") return "Negative";
    return "Neutral";
}

function displayAnalytics() {
    if (analysisData.length === 0) {
        document.getElementById("analyzeBtn").disabled = false;
        setVisible("loading", false);
        setVisible("emptyState", true);
        return;
    }

    setVisible("analyticsGrid", true);
    setVisible("resultsTable", true);
    setHidden("emptyState", true);
    setVisible("loading", false);
    document.getElementById("analyzeBtn").disabled = false;

    // do the numbers for the screen
    const vaderScores = analysisData.map(a => sentimentToValue(a.vader_sentiment));
    const textblobScores = analysisData.map(a => sentimentToValue(a.textblob_sentiment));
    const transformerScores = analysisData.map(a => sentimentToValue(a.transformer_sentiment));

    const vaderAvg = (vaderScores.reduce((a, b) => a + b, 0) / vaderScores.length).toFixed(3);
    const textblobAvg = (textblobScores.reduce((a, b) => a + b, 0) / textblobScores.length).toFixed(3);
    const transformerAvg = (transformerScores.reduce((a, b) => a + b, 0) / transformerScores.length).toFixed(3);

    const positiveCount = analysisData.filter(a => normalizeSentiment(a.vader_sentiment) === "positive").length;
    const negativeCount = analysisData.filter(a => normalizeSentiment(a.vader_sentiment) === "negative").length;
    const neutralCount = analysisData.length - positiveCount - negativeCount;

    document.getElementById("totalArticles").textContent = analysisData.length;
    document.getElementById("avgPositive").textContent = ((positiveCount / analysisData.length) * 100).toFixed(1) + "%";
    document.getElementById("avgNegative").textContent = ((negativeCount / analysisData.length) * 100).toFixed(1) + "%";
    document.getElementById("avgNeutral").textContent = ((neutralCount / analysisData.length) * 100).toFixed(1) + "%";

    document.getElementById("vaderAvg").textContent = vaderAvg;
    document.getElementById("textblobAvg").textContent = textblobAvg;
    document.getElementById("transformerAvg").textContent = transformerAvg;

    // redraw the chart
    updateChart(positiveCount, negativeCount, neutralCount);

    // fill the table again
    const resultsBody = document.getElementById("resultsBody");
    resultsBody.innerHTML = "";
    analysisData.forEach(article => {
        const row = document.createElement("tr");
        const headlineCell = document.createElement("td");
        headlineCell.className = "max-w-2xl px-4 py-4 text-stone-900";
        headlineCell.title = cleanText(article.headline);
        headlineCell.textContent = cleanText(article.headline);

        const createBadgeCell = (value) => {
            const cell = document.createElement("td");
            cell.className = "px-4 py-4";
            const badge = document.createElement("span");
            badge.className = `inline-flex px-3 py-1 text-xs font-semibold tracking-wide ${getSentimentClass(value)}`;
            badge.textContent = getSentimentLabel(value);
            cell.appendChild(badge);
            return cell;
        };

        row.appendChild(headlineCell);
        row.appendChild(createBadgeCell(article.vader_sentiment));
        row.appendChild(createBadgeCell(article.textblob_sentiment));
        row.appendChild(createBadgeCell(article.transformer_sentiment));
        resultsBody.appendChild(row);
    });
}

async function loadInitialResults() {
    const initialResults = Array.isArray(window.__INITIAL_RESULTS__) ? window.__INITIAL_RESULTS__ : [];

    if (initialResults.length > 0) {
        analysisData = initialResults;
        displayAnalytics();
        return;
    }

    try {
        const response = await fetch("/api/reports/latest");
        if (!response.ok) {
            throw new Error(`Failed to load report: ${response.status}`);
        }

        const data = await response.json();
        if (Array.isArray(data.results) && data.results.length > 0) {
            analysisData = data.results;
            displayAnalytics();
        } else {
            setVisible("emptyState", true);
            setVisible("loading", false);
        }
    } catch (error) {
        // sometimes the report file is missing and that is fine
        console.warn("Could not load saved report:", error);
        setVisible("emptyState", true);
        setVisible("loading", false);
    }
}

function updateChart(positive, negative, neutral) {
    const ctx = document.getElementById("sentimentChart").getContext("2d");
    
    if (sentimentChart) {
        sentimentChart.destroy();
    }

    sentimentChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Positive", "Negative", "Neutral"],
            datasets: [{
                data: [positive, negative, neutral],
                backgroundColor: ["#28a745", "#dc3545", "#6c757d"],
                borderColor: ["#ffffff", "#ffffff", "#ffffff"],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        padding: 15,
                        color: "#44403c",
                        font: {
                            size: 13,
                            weight: "600"
                        }
                    }
                }
            }
        }
    });
}

// Initialize
connectWebSocket();
loadInitialResults();
