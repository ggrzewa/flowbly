<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataForSEO API - Analiza Porównawcza</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .controls {
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }

        .filter-input {
            flex: 1;
            min-width: 250px;
            padding: 10px 15px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s ease;
        }

        .filter-input:focus {
            outline: none;
            border-color: #007bff;
            box-shadow: 0 0 0 3px rgba(0,123,255,0.25);
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }

        .btn-primary {
            background: #007bff;
            color: white;
        }

        .btn-primary:hover {
            background: #0056b3;
            transform: translateY(-2px);
        }

        .btn-success {
            background: #28a745;
            color: white;
        }

        .btn-success:hover {
            background: #1e7e34;
            transform: translateY(-2px);
        }

        .table-container {
            overflow-x: auto;
            max-height: 80vh;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        th, td {
            padding: 12px 8px;
            text-align: center;
            border: 1px solid #e9ecef;
            white-space: nowrap;
        }

        th {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        th:hover {
            background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
        }

        .section-header {
            background: linear-gradient(135deg, #495057 0%, #6c757d 100%) !important;
            font-weight: bold;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .first-col {
            text-align: left !important;
            font-weight: 500;
            background: #f8f9fa;
            max-width: 200px;
            position: sticky;
            left: 0;
            z-index: 5;
        }

        .available {
            background: #d4edda !important;
            color: #155724;
            font-weight: bold;
        }

        .unavailable {
            background: #f8d7da !important;
            color: #721c24;
            font-weight: bold;
        }

        .optional {
            background: #fff3cd !important;
            color: #856404;
            font-weight: bold;
        }

        .expensive {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%) !important;
            color: white !important;
            font-weight: bold;
            position: relative;
        }

        .expensive::after {
            content: "💸";
            position: absolute;
            top: 2px;
            right: 2px;
            font-size: 10px;
        }

        .cheap {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
            color: white !important;
            font-weight: bold;
            position: relative;
        }

        .cheap::after {
            content: "💚";
            position: absolute;
            top: 2px;
            right: 2px;
            font-size: 10px;
        }

        .highlight {
            background: #fff3cd !important;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 193, 7, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); }
        }

        .stats {
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
            gap: 20px;
        }

        .stat-box {
            text-align: center;
            flex: 1;
            min-width: 150px;
        }

        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }

        .stat-label {
            color: #6c757d;
            font-size: 0.9em;
            margin-top: 5px;
        }

        @media (max-width: 768px) {
            .header h1 { font-size: 1.8em; }
            .controls { flex-direction: column; }
            .filter-input { min-width: 100%; }
            th, td { padding: 8px 4px; font-size: 11px; }
        }

        .tooltip {
            position: relative;
            cursor: help;
        }

        .tooltip:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }

        .sort-arrow {
            margin-left: 5px;
            opacity: 0.5;
        }

        .sort-asc .sort-arrow::after {
            content: "▲";
            opacity: 1;
        }

        .sort-desc .sort-arrow::after {
            content: "▼";
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 DataForSEO API - Analiza Porównawcza</h1>
            <p>Kompletne porównanie endpointów i ich funkcjonalności</p>
        </div>

        <div class="controls">
            <input type="text" class="filter-input" id="searchFilter" placeholder="🔍 Szukaj funkcjonalności lub endpointu...">
            <button class="btn btn-primary" onclick="resetFilters()">🔄 Reset</button>
            <button class="btn btn-success" onclick="exportToCSV()">📊 Eksport CSV</button>
        </div>

        <div class="table-container">
            <table id="comparisonTable">
                <thead>
                    <tr>
                        <th class="first-col">Dane Zwracane</th>
                        <th class="expensive tooltip" data-tooltip="Bardzo drogi! 7x więcej niż Overview">GA_SV<br>($0.075)</th>
                        <th class="cheap tooltip" data-tooltip="Najlepszy stosunek jakości do ceny">DF_Trends<br>($0.005)</th>
                        <th class="cheap tooltip" data-tooltip="Świetny do trendów">GT_Explore<br>($0.009)</th>
                        <th class="cheap tooltip" data-tooltip="Najlepszy do podstawowych metryk">KW_Overview<br>($0.0101)</th>
                        <th class="tooltip" data-tooltip="Dobry do powiązanych słów">Related_KW<br>($0.0109)</th>
                        <th class="expensive tooltip" data-tooltip="Bardzo drogi! 8x więcej niż Overview">KW_Ideas<br>($0.08)</th>
                        <th class="tooltip" data-tooltip="Jedyny z danymi historycznymi">Historical<br>($0.0101)</th>
                        <th class="tooltip" data-tooltip="Clickstream volume">Clickstream<br>(brak ceny)</th>
                        <th class="cheap tooltip" data-tooltip="Najtańszy! Tylko intencja">Intent<br>($0.0011)</th>
                        <th class="tooltip" data-tooltip="Sugestie słów kluczowych">Suggestions<br>($0.013)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td class="section-header first-col">PODSTAWOWE DANE SŁOWA</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">keyword</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Korekta pisowni - jedyny endpoint z tą funkcją">spell (korekta pisowni)</td><td class="available highlight">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                    <tr><td class="first-col">location_code</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">language_code</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td></tr>
                    
                    <tr><td class="section-header first-col">SEARCH VOLUME & TRENDY</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">search_volume (Google Ads)</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">search_volume (clickstream)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="unavailable">❌</td><td class="available">✅</td><td class="unavailable">❌</td><td class="optional">✅*</td></tr>
                    <tr><td class="first-col">monthly_searches[]</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">search_volume_trend (%, trendy)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    
                    <tr><td class="section-header first-col">KONKURENCJA & CPC</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">competition (0-1)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">competition_level (LOW/MED/HIGH)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Tylko GA_SV ma competition_index">competition_index (0-100)</td><td class="available highlight">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                    <tr><td class="first-col">cpc (koszt za kliknięcie)</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">low_top_of_page_bid</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">high_top_of_page_bid</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    
                    <tr><td class="section-header first-col">KATEGORYZACJA & WŁAŚCIWOŚCI</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">categories[] (Google Ads)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">core_keyword</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">keyword_difficulty (0-100)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">detected_language</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    
                    <tr><td class="section-header first-col">INTENCJA WYSZUKIWANIA</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">main_intent</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Tylko Search Intent ma prawdopodobieństwa">keyword_intent (z prawdopod.)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available highlight">✅</td><td class="unavailable">❌</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Tylko Search Intent ma dodatkowe intencje">secondary_keyword_intents[]</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available highlight">✅</td><td class="unavailable">❌</td></tr>
                    
                    <tr><td class="section-header first-col">DANE DEMOGRAFICZNE</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">gender_distribution</td><td class="unavailable">❌</td><td class="available">✅</td><td class="unavailable">❌</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="optional">✅*</td></tr>
                    <tr><td class="first-col">age_distribution</td><td class="unavailable">❌</td><td class="available">✅</td><td class="unavailable">❌</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="optional">✅*</td></tr>
                    
                    <tr><td class="section-header first-col">SERP INFO</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">serp_item_types[]</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="optional">✅*</td></tr>
                    <tr><td class="first-col">se_results_count</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="optional">✅*</td></tr>
                    <tr><td class="first-col">check_url</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="optional">✅*</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="optional">✅*</td></tr>
                    
                    <tr><td class="section-header first-col">BACKLINKS</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">avg_backlinks</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">avg_dofollow</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">referring_pages/domains</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">avg_rank</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    
                    <tr><td class="section-header first-col">TRENDS & MAPY</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Wykresy trendów w czasie">trends_graph (czasowy wykres)</td><td class="unavailable">❌</td><td class="available highlight">✅</td><td class="available highlight">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Mapa geograficzna popularności">trends_map (geograficzny)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available highlight">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Zainteresowanie w podregionach">subregion_interests</td><td class="unavailable">❌</td><td class="available highlight">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Powiązane tematy">topics_list (powiązane tematy)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available highlight">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Powiązane zapytania">queries_list (powiązane zapytania)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available highlight">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                    
                    <tr><td class="section-header first-col">DANE ZNORMALIZOWANE</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">normalized_with_bing</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col">normalized_with_clickstream</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    
                    <tr><td class="section-header first-col">SPECJALNE</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">seed_keyword & seed_data</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Strukturalne powiązania słów">related_keywords[]</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available highlight">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Głębokość powiązań (0-4)">depth (poziom powiązań)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available highlight">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                    <tr><td class="first-col tooltip" data-tooltip="Dane historyczne od 2019">history[] (dane historyczne)</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available highlight">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                    
                    <tr><td class="section-header first-col">LIMITY & PARAMETRY</td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td><td class="section-header"></td></tr>
                    <tr><td class="first-col">Max keywords per request</td><td class="available">1000</td><td class="available">5</td><td class="available">5</td><td class="available">∞</td><td class="available">1</td><td class="available">200</td><td class="available">700</td><td class="available">1000</td><td class="available">1000</td><td class="available">1</td></tr>
                    <tr><td class="first-col">search_partners (Google)</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="available">✅</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td><td class="unavailable">❌</td></tr>
                </tbody>
            </table>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-value" id="totalEndpoints">10</div>
                <div class="stat-label">Endpointów</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="totalFeatures">44</div>
                <div class="stat-label">Funkcji</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="avgCost">$0.025</div>
                <div class="stat-label">Średni koszt</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="bestValue">Overview</div>
                <div class="stat-label">Najlepszy stosunek</div>
            </div>
        </div>
    </div>

    <script>
        // Search functionality
        document.getElementById('searchFilter').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#comparisonTable tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });

        // Reset filters
        function resetFilters() {
            document.getElementById('searchFilter').value = '';
            const rows = document.querySelectorAll('#comparisonTable tbody tr');
            rows.forEach(row => row.style.display = '');
        }

        // Export to CSV
        function exportToCSV() {
            const table = document.getElementById('comparisonTable');
            let csv = '';
            
            // Headers
            const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
            csv += headers.join(',') + '\n';
            
            // Data rows
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const cols = Array.from(row.querySelectorAll('td')).map(td => {
                    let text = td.textContent.trim();
                    // Replace emoji with text
                    text = text.replace('✅', 'TAK').replace('❌', 'NIE').replace('✅*', 'OPCJONALNIE');
                    return '"' + text + '"';
                });
                csv += cols.join(',') + '\n';
            });
            
            // Download
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'dataforseo_comparison.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        }

        // Add sorting functionality
        document.querySelectorAll('th').forEach((header, index) => {
            if (index === 0) return; // Skip first column
            
            header.addEventListener('click', function() {
                sortTable(index);
            });
        });

        function sortTable(columnIndex) {
            const table = document.getElementById('comparisonTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr')).filter(row => !row.querySelector('.section-header'));
            
            // Determine sort direction
            const isAsc = !table.querySelector(`th:nth-child(${columnIndex + 1})`).classList.contains('sort-asc');
            
            // Clear previous sort indicators
            table.querySelectorAll('th').forEach(th => th.classList.remove('sort-asc', 'sort-desc'));
            
            // Add sort indicator
            const header = table.querySelector(`th:nth-child(${columnIndex + 1})`);
            header.classList.add(isAsc ? 'sort-asc' : 'sort-desc');
            
            // Sort rows
            rows.sort((a, b) => {
                const aText = a.querySelector(`td:nth-child(${columnIndex + 1})`).textContent.trim();
                const bText = b.querySelector(`td:nth-child(${columnIndex + 1})`).textContent.trim();
                
                if (aText === bText) return 0;
                
                const comparison = aText.localeCompare(bText, undefined, { numeric: true });
                return isAsc ? comparison : -comparison;
            });
            
            // Re-insert sorted rows
            rows.forEach(row => tbody.appendChild(row));
        }

        // Add hover effects
        document.querySelectorAll('td').forEach(cell => {
            cell.addEventListener('mouseenter', function() {
                if (this.textContent.includes('✅') || this.textContent.includes('❌')) {
                    this.style.transform = 'scale(1.05)';
                    this.style.transition = 'transform 0.2s ease';
                }
            });
            
            cell.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        });

        // Highlight expensive endpoints on load
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(() => {
                const expensiveHeaders = document.querySelectorAll('.expensive');
                expensiveHeaders.forEach(header => {
                    header.style.animation = 'pulse 3s ease-in-out';
                });
            }, 1000);
        });
    </script>
</body>
</html>