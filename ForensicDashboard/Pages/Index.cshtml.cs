using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using ForensicDashboard.Models;
using ForensicDashboard.Services;

namespace ForensicDashboard.Pages
{
    public class IndexModel : PageModel
    {
        private readonly ForensicService _forensicService;
        private readonly ILogger<IndexModel> _logger;

        public IndexModel(ForensicService forensicService, ILogger<IndexModel> logger)
        {
            _forensicService = forensicService;
            _logger = logger;
        }

        [BindProperty]
        public IFormFile? Upload { get; set; }

        [BindProperty]
        public string CaseId { get; set; } = string.Empty;

        public InspectionResponse? Result { get; set; }
        public string? ImagePreview { get; set; }

        public void OnGet()
        {
        }

        public async Task<IActionResult> OnPostAsync()
        {
            if (Upload == null || string.IsNullOrEmpty(CaseId))
            {
                return Page();
            }

            // Create a preview for the UI
            using (var ms = new MemoryStream())
            {
                await Upload.CopyToAsync(ms);
                var bytes = ms.ToArray();
                ImagePreview = $"data:{Upload.ContentType};base64,{Convert.ToBase64String(bytes)}";
            }

            _logger.LogInformation("Processing upload for Case ID: {CaseId}", CaseId);
            Result = await _forensicService.InspectImageAsync(Upload, CaseId);

            if (Result == null)
            {
                ModelState.AddModelError(string.Empty, "The AI Inspection service is currently unavailable. Please ensure the Python API is running.");
            }

            return Page();
        }
    }
}
