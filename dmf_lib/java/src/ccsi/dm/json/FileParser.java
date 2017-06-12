package ccsi.dm.json;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;

import org.apache.chemistry.opencmis.commons.impl.json.JSONObject;
import org.apache.chemistry.opencmis.commons.impl.json.parser.JSONParseException;
import org.apache.chemistry.opencmis.commons.impl.json.parser.JSONParser;

public class FileParser {
	public HashMap<String, Object> sinterConfigParser(String fileName) {
		
		File file = new File(fileName);
		HashMap<String, Object> results = new HashMap<String, Object>();
		
		try {

			JSONParser parser = new JSONParser();
			JSONObject jsonObject = (JSONObject) parser.parse(new FileReader(
					file));

			// For sinter config
			for (String topLevelKey : jsonObject.keySet()) {

				if (topLevelKey.equals("inputs")
						|| topLevelKey.equals("outputs")
						|| topLevelKey.equals("settings")
						|| topLevelKey.equals("input_files")
						|| topLevelKey.equals("inputs")) {
					JSONObject topLevelValueObjects = (JSONObject) jsonObject
							.get(topLevelKey);
					
					HashMap<String, Object> dictionary = new HashMap<String, Object>();
					for (String key : topLevelValueObjects.keySet()) {
						
						JSONObject subObject = (JSONObject) topLevelValueObjects.get(key);
						HashMap<String, Object> subdictionary = new HashMap<String, Object>();
						for (String subkey : subObject.keySet()) {							
							subdictionary.put(subkey, subObject.get(subkey));							
						}
						
						dictionary.put(key, subdictionary);						
					}
					results.put(topLevelKey, dictionary);
					
				} else if (topLevelKey.equals("title")
						|| topLevelKey.equals("description")
						|| topLevelKey.equals("author")
						|| topLevelKey.equals("filetype")
						|| topLevelKey.equals("version")
						|| topLevelKey.equals("date")) {
					String value = jsonObject.get(topLevelKey).toString();
					results.put(topLevelKey, value);
					
				} else {
					String value = jsonObject.get(topLevelKey).toString();
					results.put(topLevelKey, value);
				}

			}			
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (JSONParseException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return results;
	}
}
