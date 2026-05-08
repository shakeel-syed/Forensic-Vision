using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Collections.Generic;

namespace ForensicClient
{
    // --- 1. Model Classes to match the Python API Response ---

    public class DetectionInfo
    {
        [JsonPropertyName("label")]
        public string Label { get; set; } = string.Empty;

        [JsonPropertyName("box_2d")]
        public List<int> Box2d { get; set; } = new();

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;
    }

    public class AttemptRecord
    {
        [JsonPropertyName("iteration")]
        public int Iteration { get; set; }

        [JsonPropertyName("analysis")]
        public string Analysis { get; set; } = string.Empty;

        [JsonPropertyName("score")]
        public int Score { get; set; }

        [JsonPropertyName("decision")]
        public string Decision { get; set; } = string.Empty;

        [JsonPropertyName("reasoning")]
        public string Reasoning { get; set; } = string.Empty;

        [JsonPropertyName("detections")]
        public List<DetectionInfo> Detections { get; set; } = new();
    }

    public class InspectionResponse
    {
        [JsonPropertyName("case_id")]
        public string? CaseId { get; set; }

        [JsonPropertyName("image_name")]
        public string ImageName { get; set; } = string.Empty;

        [JsonPropertyName("final_decision")]
        public string FinalDecision { get; set; } = string.Empty;

        [JsonPropertyName("final_score")]
        public int FinalScore { get; set; }

        [JsonPropertyName("total_attempts")]
        public int TotalAttempts { get; set; }

        [JsonPropertyName("detailed_analysis")]
        public string DetailedAnalysis { get; set; } = string.Empty;

        [JsonPropertyName("detections")]
        public List<DetectionInfo> Detections { get; set; } = new();

        [JsonPropertyName("history")]
        public List<AttemptRecord> History { get; set; } = new();
    }

    // --- 2. Main Client Application ---

    class Program
    {
        private static readonly HttpClient client = new HttpClient();
        private const string BaseUrl = "http://localhost:8000";

        static async Task Main(string[] args)
        {
            Console.Clear();
            Console.WriteLine("📍 Forensic Evidence Client");
            Console.WriteLine("====================================\n");

            // 1. Check API Status
            bool isOnline = await CheckHealthAsync();
            if (!isOnline) return;

            // 2. Perform Forensic Inspection
            // Using relative path to assets folder in the root
            string imagePath = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "assets", "sample.jpg");
            
            // If the above path doesn't work (depending on where it's run from), try root
            if (!File.Exists(imagePath)) imagePath = "assets/sample.jpg"; 

            if (File.Exists(imagePath))
            {
                await InspectImageAsync(imagePath, "CS-2026-ALPHA");
            }
            else
            {
                Console.WriteLine($"[Error] Could not find image at: {Path.GetFullPath(imagePath)}");
            }

            Console.WriteLine("\nSession Ended. Press any key...");
            Console.ReadKey();
        }

        static async Task<bool> CheckHealthAsync()
        {
            try
            {
                var response = await client.GetAsync($"{BaseUrl}/health");
                if (response.IsSuccessStatusCode)
                {
                    Console.WriteLine("✅ System Online (Gemini Engine Ready)\n");
                    return true;
                }
            }
            catch
            {
                Console.WriteLine("❌ System Offline. Please run 'python src/ForensicAPI.py' first.");
            }
            return false;
        }

        static async Task InspectImageAsync(string filePath, string caseId)
        {
            Console.WriteLine($"🚀 Analyzing Evidence: {Path.GetFileName(filePath)}...");
            
            try
            {
                using var form = new MultipartFormDataContent();
                using var fileStream = File.OpenRead(filePath);
                using var streamContent = new StreamContent(fileStream);
                
                streamContent.Headers.ContentType = new MediaTypeHeaderValue("image/jpeg");
                form.Add(streamContent, "file", Path.GetFileName(filePath));

                // Send request (FastAPI accepts case_id as a query parameter)
                string url = $"{BaseUrl}/inspect?case_id={Uri.EscapeDataString(caseId)}";
                var response = await client.PostAsync(url, form);
                
                if (response.IsSuccessStatusCode)
                {
                    string json = await response.Content.ReadAsStringAsync();
                    
                    // Deserialize into our C# objects
                    var result = JsonSerializer.Deserialize<InspectionResponse>(json);

                    if (result != null)
                    {
                        DisplayResult(result);
                    }
                }
                else
                {
                    Console.WriteLine($"❌ API Error: {response.StatusCode}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Client Error: {ex.Message}");
            }
        }

        static void DisplayResult(InspectionResponse res)
        {
            Console.WriteLine("\n--- FORENSIC REPORT ---");
            Console.WriteLine($"Case ID:    {res.CaseId}");
            Console.WriteLine($"Decision:   {(res.FinalDecision == "Approve" ? "✅ APPROVED" : "❌ RETRY")}");
            Console.WriteLine($"Score:      {res.FinalScore}/10");
            Console.WriteLine($"Attempts:   {res.TotalAttempts}");
            Console.WriteLine($"Detections: {res.Detections.Count}");
            Console.WriteLine("\nAnalysis:");
            Console.WriteLine(res.DetailedAnalysis);
            
            if (res.Detections.Count > 0)
            {
                Console.WriteLine("\n📍 Detected Points:");
                foreach (var det in res.Detections)
                {
                    Console.WriteLine($"- {det.Label}: {det.Description} (Box: {string.Join(",", det.Box2d)})");
                }
            }
            Console.WriteLine("-----------------------");
        }
    }
}
