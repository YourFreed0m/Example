using System;
using System.Numerics;
using Raylib_cs;
using NAudio.Wave;

namespace Audiosurf2
{
    public class Game
    {
        private const int ScreenWidth = 1280;
        private const int ScreenHeight = 800;

        private Track _track = new Track();
        private Rider _rider = new Rider();
        private AudioAnalyzer _audio = new AudioAnalyzer();

        public void Run()
        {
            Raylib.InitWindow(ScreenWidth, ScreenHeight, "Audiosurf2 Mini (C#)");
            Raylib.SetTargetFPS(120);

            _rider.Position = new Vector3(0, 0.35f, 0);

            while (!Raylib.WindowShouldClose())
            {
                Update();
                Draw();
            }
            _audio.Dispose();
            Raylib.CloseWindow();
        }

        private void Update()
        {
            // Mouse-only controls
            float nx = Raylib.GetMouseX() / (float)ScreenWidth; // 0..1
            int lane = Math.Clamp((int)MathF.Round(nx * 2f) - 1, -1, 1);
            _rider.TargetX = lane * Track.LaneWidth;

            float wheel = Raylib.GetMouseWheelMove();
            if (wheel != 0) _track.Speed = Math.Clamp(_track.Speed + (wheel > 0 ? 2 : -2), 4, 40);

            if (Raylib.IsMouseButtonPressed(MouseButton.MOUSE_LEFT_BUTTON) && _rider.OnGround)
                _rider.Jump();

            _rider.Update(Raylib.GetFrameTime());
            _track.Update(Raylib.GetFrameTime(), _audio);
        }

        private void Draw()
        {
            Raylib.BeginDrawing();
            Raylib.ClearBackground(new Color(11, 14, 19, 255));

            _track.Draw();
            _rider.Draw();

            Raylib.DrawText("Мышь: X — полоса, колесо — скорость, ЛКМ — прыжок", 12, 12, 20, Color.LIGHTGRAY);
            Raylib.EndDrawing();
        }
    }

    public class Track
    {
        public const float LaneWidth = 120f; // pixel lane width on screen projection
        public float Speed { get; set; } = 10f;
        private float _zOffset = 0f;
        private readonly System.Collections.Generic.List<Pickup> _pickups = new();
        private float _spawnTimer = 0f;

        public void Update(float dt, AudioAnalyzer audio)
        {
            _zOffset += Speed * dt;

            float intensity = audio.GetBassIntensity();
            _spawnTimer += dt * (0.5f + intensity * 4f);
            if (_spawnTimer >= 1f)
            {
                _spawnTimer = 0f;
                int lane = Raylib.GetRandomValue(-1, 1);
                _pickups.Add(new Pickup { Lane = lane, Z = -600f - Raylib.GetRandomValue(0, 300) });
            }

            // move pickups
            for (int i = _pickups.Count - 1; i >= 0; i--)
            {
                _pickups[i].Z += Speed * dt * 60f;
                if (_pickups[i].Z > 100f) _pickups.RemoveAt(i);
            }
        }

        public void Draw()
        {
            // Lanes
            int centerX = ScreenWidth / 2;
            int groundY = (int)(ScreenHeight * 0.7f);
            for (int i = -1; i <= 1; i++)
            {
                int x = centerX + (int)(i * LaneWidth);
                Raylib.DrawRectangle(x - (int)(LaneWidth / 2), groundY - 600, (int)LaneWidth, 800, new Color(28, 36, 48, 255));
            }

            // Pickups
            foreach (var p in _pickups)
            {
                int x = centerX + (int)(p.Lane * LaneWidth);
                int y = groundY - (int)(p.Z);
                Raylib.DrawCircle(x, y, 8, new Color(0, 209, 255, 255));
            }
        }

        private struct Pickup { public int Lane; public float Z; }
    }

    public class Rider
    {
        public Vector3 Position { get; set; }
        public float TargetX { get; set; } = 0f;
        public bool OnGround => Position.Y <= 0.351f;
        private float _vy = 0f;

        public void Jump()
        {
            _vy = 6f;
        }

        public void Update(float dt)
        {
            Position = new Vector3(MathF.Lerp(Position.X, TargetX, MathF.Min(1f, dt * 10f)), Position.Y, Position.Z);
            if (_vy > 0 || Position.Y > 0.35f)
            {
                Position = new Vector3(Position.X, Position.Y + _vy * dt, Position.Z);
                _vy -= 18f * dt;
                if (Position.Y <= 0.35f) { Position = new Vector3(Position.X, 0.35f, Position.Z); _vy = 0f; }
            }
        }

        public void Draw()
        {
            int cx = Raylib.GetScreenWidth() / 2;
            int groundY = (int)(Raylib.GetScreenHeight() * 0.7f);
            int x = cx + (int)(Position.X);
            int y = groundY - (int)(Position.Y * 100f);
            Raylib.DrawCircle(x, y, 12, new Color(255, 204, 0, 255));
        }
    }

    public class AudioAnalyzer : IDisposable
    {
        private IWavePlayer? _output;
        private AudioFileReader? _reader;
        private float _bassIntensity = 0f;
        private readonly object _lock = new();

        public AudioAnalyzer()
        {
            // No auto-play; user will set file via dialog — omitted for brevity.
        }

        public void Dispose()
        {
            _output?.Stop();
            _reader?.Dispose();
            _output?.Dispose();
        }

        public float GetBassIntensity()
        {
            // Placeholder: return small oscillation to simulate beats if no audio loaded
            _bassIntensity = 0.3f + 0.2f * MathF.Sin((float)Raylib.GetTime() * 3f);
            return Math.Clamp(_bassIntensity, 0f, 1f);
        }
    }

    public static class Program
    {
        [STAThread]
        public static void Main()
        {
            new Game().Run();
        }
    }
}