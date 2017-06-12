package ccsi.dm.json;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import org.json.JSONArray;
import org.json.JSONObject;

public class JSONProcessor {

	public Map<String, Object> jsonObject2Map(JSONObject jsonObject) {
		if (JSONObject.NULL == jsonObject) {
			return new HashMap<String, Object>();
		} else {
			return convertJSONObject2Map(jsonObject);
		}
	}

	private Map<String, Object> convertJSONObject2Map(JSONObject jsonObject) {
		Map<String, Object> jsonMap = new HashMap<String, Object>();
		Iterator<String> keys = jsonObject.keys();
		while (keys.hasNext()) {
			String key = keys.next();
			Object value = jsonObject.get(key);
			if (value instanceof JSONObject) {
				jsonMap.put(key, convertJSONObject2Map((JSONObject) value));
			} else if (value instanceof JSONArray) {
				jsonMap.put(key, convertJSONArray2ArrayList((JSONArray) value));
			} else {
				jsonMap.put(key, value);
			}
		}

		return jsonMap;
	}

	private List<Object> convertJSONArray2ArrayList(JSONArray array) {
		List<Object> jsonArrayList = new ArrayList<Object>();
		for (Object value : array) {
			if (value instanceof JSONObject) {
				jsonArrayList.add(convertJSONObject2Map((JSONObject) value));
			} else if (value instanceof JSONArray) {
				jsonArrayList.add(convertJSONArray2ArrayList((JSONArray) value));
			} else {
				jsonArrayList.add(value);
			}
		}
		return jsonArrayList;
	}
}
