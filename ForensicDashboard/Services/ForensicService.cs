using System.Net.Http.Headers;
using System.Text.Json;
using ForensicDashboard.Models;

namespace ForensicDashboard.Services
{
    public class ForensicService
    {
        private readonly HttpClient _http;
        private readonly ILogger<ForensicService> _logger;

        public ForensicService(HttpClient http, ILogger<ForensicService> logger)
        {
            _http = http;
            _logger = logger;
        }

        public async Task<InspectionResponse?> InspectImageAsync(IFormFile file, string caseId)
        {
            try
            {
                using var content = new MultipartFormDataContent();
                using var stream = file.OpenReadStream();
                var fileContent = new StreamContent(stream);
                
                fileContent.Headers.ContentType = new MediaTypeHeaderValue(file.ContentType);
                content.Add(fileContent, "file", file.FileName);

                _logger.LogInformation("STEP 1: Sending request to Python API (Case: {CaseId})", caseId);
                
                var response = await _http.PostAsync($"/inspect?case_id={Uri.EscapeDataString(caseId)}", content);
                
                _logger.LogInformation("STEP 2: Received response status: {StatusCode}", response.StatusCode);

                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
                    return JsonSerializer.Deserialize<InspectionResponse>(json);
                }
                else
                {
                    var error = await response.Content.ReadAsStringAsync();
                    _logger.LogError("API Error: {StatusCode} - {Error}", response.StatusCode, error);
                }
            }
            catch (TaskCanceledException)
            {
                _logger.LogError("The request timed out. The AI took longer than 180 seconds.");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to connect to Forensic API at http://localhost:8000. Is it running?");
            }
            
            return null;
        }
    }
}
