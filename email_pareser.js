const processIntegration = async (integration) => {
    try {
      if (integration.isGmailIntegrated) {
        const MessagesRetrieved = [];
        console.log("Integration:", integration);
        const email = integration.email;
        const user_id = integration.user_id;
        const team_id = integration.team_id;
        const refresh_tokens = integration.refreshToken;
        const access_tokens = integration.Authorisation_Token;
        const limitExhausted = integration.FeedbackCount;
        let plan = (await getUserLimit(team_id)).plan;
        let userLimit = Plan_Limit(plan);
  
        let end_on = (await getUserLimit(team_id)).end_on;
        let today = new Date().getTime();
        let endDate = new Date(end_on).getTime();
        let clients = client.client;
        let limitLeft = userLimit - limitExhausted;
        let currentCount = 0;
        clients.setCredentials({
          access_token: access_tokens,
          refresh_token: refresh_tokens,
        });
        const gmail = google.gmail({ version: "v1", auth: clients });
        if (limitLeft <= 0) {
          return;
        }
        try {
          // Fetch the latest message IDs and thread IDs from MongoDB
          const messageData = await GmailData.find({
            team_id: team_id,
            email_id: email,
          }).select({ message_id: 1, thread_id: 1 });
  
          const existingMessageIds = new Set(
            messageData.map((data) => data.message_id)
          );
          console.log("Existing message IDs:", existingMessageIds);
  
          let firstTimeFetch = existingMessageIds.size === 0;
          let nextPageToken = null;
          let shouldBreak = false; // Add a flag to break out of the loop
  
          do {
            const response = await gmail.users.messages.list({
              userId: "me",
              maxResults: 100,
              includeSpamTrash: false,
              q: "is:inbox",
              fields: "messages(id, threadId), nextPageToken",
              pageToken: nextPageToken,
            });
  
            console.log(response.data.messages);
  
            for (let message of response.data.messages) {
              const messageId = message.id;
              const threadId = message.threadId;
              if (firstTimeFetch) {
                shouldBreak = true;
              }
  
              if (!firstTimeFetch && existingMessageIds.has(messageId)) {
                shouldBreak = true;
                break;
              }
  
              // Fetch message details
              const messageResponse = await gmail.users.messages.get({
                userId: "me",
                id: messageId,
                format: "full",
              });
  
              const { payload } = messageResponse.data;
              const { headers, body, parts } = payload;
  
              const subjectHeader = headers.find(
                (header) => header.name === "Subject"
              );
              const fromHeader = headers.find((header) => header.name === "From");
              const dateHeader = headers.find((header) => header.name === "Date");
              const subject = subjectHeader ? subjectHeader.value : "No Subject";
              const sender = fromHeader ? fromHeader.value : "Unknown Sender";
              const date = dateHeader
                ? new Date(dateHeader.value).toISOString().replace("Z", "+00:00")
                : "Unknown Date";
  
              console.log(
                "Message details:",
                subject,
                sender,
                date,
                messageId,
                threadId
              );
  
              let combinedMessage = `Subject: ${subject}\n\n`;
  
              if (parts) {
                parts.forEach((part) => {
                  // Log the part for debugging
                  if (part.mimeType === "text/plain" && part.body.data) {
                    const decodedPart = Buffer.from(
                      part.body.data,
                      "base64"
                    ).toString("utf-8");
                    const cleanedText = decodedPart
                      .replace(/(\r\n|\n|\r)+/g, " ")
                      .trim();
                    combinedMessage += cleanedText + " ";
                  } else if (part.mimeType === "text/html" && part.body.data) {
                    const decodedPart = Buffer.from(
                      part.body.data,
                      "base64"
                    ).toString("utf-8");
                    const $ = cheerio.load(decodedPart);
                    $("style, script").remove();
                    const plainText = $.text().replace(/\s+/g, " ").trim();
                    combinedMessage += plainText + " ";
                  }
                });
  
                combinedMessage = combinedMessage.trim();
  
                console.log("Combined message:", combinedMessage);
  
                MessagesRetrieved.push({
                  sender,
                  date,
                  combinedMessage,
                  messageId,
                  threadId, // Include threadId in the retrieved messages
                });
              } else if (body && body.data) {
                // Log the body for debugging
                const Messagebody = Buffer.from(body.data, "base64").toString(
                  "utf-8"
                );
                const $ = cheerio.load(Messagebody);
                $("style, script").remove();
                const plainText = $.text().replace(/\s+/g, " ").trim();
                combinedMessage += plainText;
  
                console.log("Combined message:", combinedMessage);
                MessagesRetrieved.push({
                  sender,
                  date,
                  combinedMessage,
                  messageId,
                  threadId, // Include threadId in the retrieved messages
                });
              }
  
              await new Promise((resolve) => setTimeout(resolve, 5));
            }
  
            if (shouldBreak) {
              break; // Break out of the outer do-while loop
            }
  
            nextPageToken = response.data.nextPageToken;
          } while (nextPageToken);
          console.log("Messages retrieved:", MessagesRetrieved.length);
  
          for (let i = MessagesRetrieved.length - 1; i >= 0; i--) {
            console.log("Current count:", currentCount);
            let message = MessagesRetrieved[i];
            if (currentCount >= limitLeft) {
              console.log("Limit exhausted, breaking the loop");
              break;
            }
            if (
              message.sender &&
              message.date &&
              message.combinedMessage !== ""
            ) {
              let newFeedback = new Feedback({
                user_id,
                team_id,
                source: "Gmail",
                src_datetime: message.date,
                src_username: message.sender,
                src_content: message.combinedMessage,
                thread_id: message.threadId, // Store threadId in Feedback collection
              });
              let data = new GmailData({
                user_id,
                email_id: email,
                team_id,
                message_id: message.messageId,
                thread_id: message.threadId, // Store threadId in GmailData collection
              });
              await data.save();
              await newFeedback.save();
              currentCount++;
            } else {
              console.log("Skipping message:", message);
            }
          }
          console.log("Current count:", currentCount);
          await gmailintegrations.findByIdAndUpdate(integration._id, {
            $inc: { FeedbackCount: currentCount },
          });
        } catch (error) {
          console.error("Error fetching Gmail data:", error);
          throw error;
        }
      }
    } catch (err) {
      console.error("Error processing integration:", err);
      throw err;
    }
  };