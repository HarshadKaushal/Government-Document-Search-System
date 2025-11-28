# Quick view embedding - fastest method
$response = Invoke-RestMethod -Uri "http://localhost:9200/government_documents/_search" -Method Post -Body (@{
    size = 1
    _source = @('doc_id', 'title', 'chunk_id', 'embedding')
    query = @{match_all = @{}}
} | ConvertTo-Json -Compress) -ContentType "application/json"

$hit = $response.hits.hits[0]
$src = $hit._source
$emb = $src.embedding

Write-Host "`n=== VECTOR EMBEDDING ===" -ForegroundColor Green
Write-Host "Document ID: $($src.doc_id)" -ForegroundColor Cyan
Write-Host "Title: $($src.title)" -ForegroundColor Cyan
Write-Host "Chunk ID: $($src.chunk_id)" -ForegroundColor Cyan
Write-Host "Embedding Dimension: $($emb.Count)" -ForegroundColor Cyan
Write-Host "`nFirst 20 values: $($emb[0..19] -join ', ')" -ForegroundColor Yellow
Write-Host "`nFull Vector (384 dimensions):" -ForegroundColor Yellow
$emb

