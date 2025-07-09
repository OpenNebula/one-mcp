/*
 * Copyright 2002-2025, OpenNebula Project, OpenNebula Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// This transform is used to extract the function call and its arguments from the output of the MCP server.
// It is used to assert the function call and its arguments in the tests.

module.exports = (output) => {
  try {
    // Parse the JSON array of tool calls
    const calls = Array.isArray(output) ? output : JSON.parse(output);
    
    if (!calls || calls.length === 0) {
      return [];
    }
    
    // Extract all function calls and parse their arguments
    const functionCalls = calls.map(call => {
      if (!call || !call.function) {
        return null;
      }
      
      const functionName = call.function.name;
      const args = typeof call.function.arguments === 'string' 
        ? JSON.parse(call.function.arguments) 
        : call.function.arguments;
      
      return {
        function: functionName,
        arguments: args
      };
    }).filter(call => call !== null);
    
    return functionCalls;
  } catch (e) {
    return [];
  }
}; 