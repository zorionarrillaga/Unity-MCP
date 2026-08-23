/*
┌──────────────────────────────────────────────────────────────────┐
│  Author: Ivan Murzak (https://github.com/IvanMurzak)             │
│  Repository: GitHub (https://github.com/IvanMurzak/Unity-MCP)    │
│  Copyright (c) 2025 Ivan Murzak                                  │
│  Licensed under the Apache License, Version 2.0.                 │
│  See the LICENSE file in the project root for more information.  │
└──────────────────────────────────────────────────────────────────┘
*/

#nullable enable
using System.Collections;
using NUnit.Framework;
using R3;
using UnityEngine.TestTools;

namespace com.IvanMurzak.Unity.MCP.LLM.Tests
{
    [TestFixture]
    public class ComponentTests : BaseEvalTest
    {
        [UnityTest]
        public IEnumerator Agent_CanChangeLightColorToRed()
        {
            // 1. Setup the Scene
            var lightGo = new UnityEngine.GameObject("TestLight");
            var light = lightGo.AddComponent<UnityEngine.Light>();
            light.color = UnityEngine.Color.white;

            // 2. Run the agent evaluation
            var prompt = "Find the light named 'TestLight' in the scene and change its Light component color to red (r: 1, g: 0, b: 0, a: 1).";
            yield return RunAgentEval(prompt);

            // 3. Verify the AI did its job
            Assert.AreEqual(UnityEngine.Color.red, light.color, "The AI failed to change the light to red.");

            // Cleanup
            UnityEngine.Object.DestroyImmediate(lightGo);
        }
    }
}
