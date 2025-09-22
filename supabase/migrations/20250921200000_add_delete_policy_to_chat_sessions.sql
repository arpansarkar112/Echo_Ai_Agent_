-- Add a policy to allow users to delete their own chat sessions
CREATE POLICY "Allow users to delete their own chat sessions" ON public.chat_sessions
FOR DELETE USING ((auth.uid() = user_id));
