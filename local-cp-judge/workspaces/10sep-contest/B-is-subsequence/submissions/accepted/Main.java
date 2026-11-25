import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        List<String> tokens = new ArrayList<>();
        String line;
        while ((line = br.readLine()) != null) {
            StringTokenizer st = new StringTokenizer(line);
            while (st.hasMoreTokens()) {
                tokens.add(st.nextToken());
            }
        }

        String s = tokens.size() >= 1 ? tokens.get(0) : "";
        String t = tokens.size() >= 2 ? tokens.get(1) : "";

        int i = 0;
        for (int j = 0; j < t.length() && i < s.length(); j++) {
            if (s.charAt(i) == t.charAt(j)) {
                i++;
            }
        }
        System.out.println(i == s.length() ? "true" : "false");
    }
}
