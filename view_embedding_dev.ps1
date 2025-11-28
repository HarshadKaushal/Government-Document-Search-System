# PowerShell script to view embeddings using Elasticsearch Dev Tools API

$index = "government_documents"
$esUrl = "http://localhost:9200"

Write-Host "=== Viewing Vector Embeddings from Elasticsearch ===" -ForegroundColor Green
Write-Host ""

# Function to get embedding
function Get-Embedding {
    param(
        [string]$DocId = $null,
        [int]$Size = 1
    )
    
    $body = @{
        size = $Size
        _source = @("doc_id", "title", "chunk_id", "embedding", "text_chunk")
    }
    
    if ($DocId) {
        $body.query = @{
            term = @{
                doc_id = $DocId
            }
        }
        Write-Host "Fetching embedding for document: $DocId" -ForegroundColor Yellow
    } else {
        $body.query = @{
            match_all = @{}
        }
        Write-Host "Fetching first available embedding..." -ForegroundColor Yellow
    }
    
    $jsonBody = $body | ConvertTo-Json -Depth 10
    $url = "$esUrl/$index/_search?pretty"
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method Post -Body $jsonBody -ContentType "application/json"
        
        if ($response.hits.hits.Count -eq 0) {
            Write-Host "No documents found!" -ForegroundColor Red
            return
        }
        
        $hit = $response.hits.hits[0]._source
        $embedding = $hit.embedding
        
        Write-Host ""
        Write-Host "=== EMBEDDING DETAILS ===" -ForegroundColor Green
        Write-Host "Document ID: $($hit.doc_id)" -ForegroundColor Cyan
        Write-Host "Title: $($hit.title)" -ForegroundColor Cyan
        Write-Host "Chunk ID: $($hit.chunk_id)" -ForegroundColor Cyan
        Write-Host "Embedding Dimension: $($embedding.Count)" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "First 20 values:" -ForegroundColor Yellow
        $embedding[0..19] -join ", "
        Write-Host ""
        Write-Host "Last 10 values:" -ForegroundColor Yellow
        $embedding[-10..-1] -join ", "
        Write-Host ""
        Write-Host "Vector Statistics:" -ForegroundColor Yellow
        Write-Host "  Min: $([Math]::Round(($embedding | Measure-Object -Minimum).Minimum, 6))"
        Write-Host "  Max: $([Math]::Round(($embedding | Measure-Object -Maximum).Maximum, 6))"
        Write-Host "  Mean: $([Math]::Round(($embedding | Measure-Object -Average).Average, 6))"
        Write-Host ""
        
        if ($hit.text_chunk) {
            Write-Host "Text Preview (first 200 chars):" -ForegroundColor Yellow
            $hit.text_chunk.Substring(0, [Math]::Min(200, $hit.text_chunk.Length))
        }
        
    } catch {
        Write-Host "Error: $_" -ForegroundColor Red
    }
}

# Check if doc_id provided as argument
if ($args.Count -gt 0) {
    Get-Embedding -DocId $args[0]
} else {
    Get-Embedding
}

Write-Host ""
Write-Host "Usage: .\view_embedding_dev.ps1 [doc_id]" -ForegroundColor Gray

