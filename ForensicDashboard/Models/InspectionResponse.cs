using System.Text.Json.Serialization;

namespace ForensicDashboard.Models
{
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
}
